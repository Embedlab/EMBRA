from flask import Flask, request, jsonify, render_template_string
import can
from threading import Thread
import os
import csv
from datetime import datetime

bus_can0 = None
bus_can1 = None

logging_threads = {}
logging_can_active = {"can0": False, "can1": False}

def log_can_data(CAN_interface):
    """
    Logs CAN messages from can0 and can1 to CSV files in the specified directory.
    """
    # global logging_can0_active, logging_can1_active
    # if CAN_interface == "can0":
    #     logging_can0_active = True
    # elif CAN_interface == "can1":
    #     logging_can1_active = True

    logging_dir = f"/home/pi/{CAN_interface}"

    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # Przygotowanie plików CSV
    csv_files = {
        CAN_interface: open(os.path.join(logging_dir, f"{CAN_interface}_{timestamp}.csv"), mode='a', newline=''),
    }

    csv_writers = {
        CAN_interface: csv.DictWriter(csv_files[CAN_interface], fieldnames=['Timestamp', 'CAN ID', 'Data']),
    }

    # Dodanie nagłówków, jeśli pliki są puste
    for channel, file in csv_files.items():
        if os.stat(file.name).st_size == 0:
            csv_writers[channel].writeheader()

    # Inicjalizacja interfejsów CAN
    try:
        bus_can = can.interface.Bus(channel=CAN_interface, interface='socketcan')
    except Exception as e:
        print(f"[ERROR] Failed to initialize CAN interfaces: {e}")
        return

    try:
        while logging_can_active[CAN_interface]:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            # Odczyt wiadomości z can0 i can1
            for bus, channel_name in [(bus_can, CAN_interface)]:
                try:
                    message = bus.recv(timeout=0.01)
                    if message:
                        can_data = {
                            'Timestamp': timestamp,
                            'CAN ID': hex(message.arbitration_id),
                            'Data': message.data.hex() if message.data else 'No Data'
                        }
                        csv_writers[channel_name].writerow(can_data)
                        csv_files[channel_name].flush()  # Wymuszony zapis na dysk
                except can.CanError as e:
                    print(f"[ERROR] CAN error on {channel_name}: {e}")
                    continue
    finally:
        # Zamknięcie interfejsów CAN i plików CSV
        bus_can.shutdown()

        for file in csv_files.values():
            file.close()
        print("[INFO] CAN logging stopped.")

def initialize_can(request):
    """
    Initializes the specified CAN bus (can0 or can1).
    """

    global bus_can0, bus_can1

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    interface = data.get("interface")  # 'can0' or 'can1'
    
    if interface not in ["can0", "can1"]:
        return jsonify({"status": "error", "message": "Invalid CAN interface. Use 'can0' or 'can1'."}), 400

    try:
        if interface == "can0" and bus_can0 is None:
            bus_can0 = can.interface.Bus(channel='can0', interface='socketcan')
        elif interface == "can1" and bus_can1 is None:
            bus_can1 = can.interface.Bus(channel='can1', interface='socketcan')
        
        return jsonify({"status": "success", "message": f"{interface} initialized."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def can_status():
    """
    Returns the status of CAN interfaces (can0 and can1).
    """
    global bus_can0, bus_can1  # Upewniamy się, że odwołujemy się do zmiennych globalnych

    status = {
        "can0": "initialized" if 'bus_can0' in globals() and bus_can0 else "not initialized",
        "can1": "initialized" if 'bus_can1' in globals() and bus_can1 else "not initialized"
    }

    return jsonify({"status": "success", "message": "CAN interface statuses retrieved.", "interfaces": status}), 200

def can_send(request):
    """
    Sends a CAN message to the specified CAN interface.
    """
    global bus_can0, bus_can1  # Upewniamy się, że odwołujemy się do zmiennych globalnych

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    # Pobieranie danych z żądania
    interface = data.get("interface")  # 'can0' lub 'can1'
    message_id = data.get("id")  # ID wiadomości CAN
    message_data = data.get("data")  # Dane wiadomości CAN (w tablicy)

    # Walidacja wejścia
    if interface not in ["can0", "can1"]:
        return jsonify({"status": "error", "message": "Invalid CAN interface. Use 'can0' or 'can1'."}), 400
    if not isinstance(message_id, int) or message_id < 0 or message_id > 0x7FF:
        return jsonify({"status": "error", "message": "Invalid CAN ID. Must be an integer between 0 and 0x7FF."}), 400
    if not isinstance(message_data, list) or not all(isinstance(byte, int) and 0 <= byte <= 0xFF for byte in message_data):
        return jsonify({"status": "error", "message": "Invalid CAN data. Must be a list of integers between 0 and 255."}), 400

    # Sprawdzenie, czy interfejs jest zainicjalizowany
    if interface == "can0" and 'bus_can0' not in globals():
        return jsonify({"status": "error", "message": "CAN interface 'can0' not initialized."}), 400
    if interface == "can1" and 'bus_can1' not in globals():
        return jsonify({"status": "error", "message": "CAN interface 'can1' not initialized."}), 400

    try:
        # Wybór odpowiedniego interfejsu
        bus = bus_can0 if interface == "can0" else bus_can1

        # Wysyłanie wiadomości CAN
        can_msg = can.Message(arbitration_id=message_id, data=message_data, is_extended_id=False)
        bus.send(can_msg)

        return jsonify({
            "status": "success",
            "message": f"Message sent on {interface}.",
            "details": {"id": message_id, "data": message_data}
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to send CAN message: {str(e)}"}), 500

def log_can(request):
    """
    Starts or stops CAN logging for the specified interface.
    """
    global logging_threads, logging_active

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    interface = data.get("interface")
    action = data.get("action")

    if interface not in ["can0", "can1"]:
        return jsonify({"status": "error", "message": "Invalid CAN interface. Use 'can0' or 'can1'."}), 400
    if action not in ["start", "stop"]:
        return jsonify({"status": "error", "message": "Invalid action. Use 'start' or 'stop'."}), 400

    if action == "start":
        if logging_can_active[interface]:
            return jsonify({"status": "error", "message": f"Logging is already active for {interface}."}), 400

        logging_can_active[interface] = True
        thread = Thread(target=log_can_data, args=(interface,), daemon=True)
        logging_threads[interface] = thread
        thread.start()
        return jsonify({"status": "success", "message": f"Started logging for {interface}."}), 200

    elif action == "stop":
        if not logging_can_active[interface]:
            return jsonify({"status": "error", "message": f"Logging is not active for {interface}."}), 400

        logging_can_active[interface] = False
        logging_threads[interface].join()  # Wait for thread to finish
        return jsonify({"status": "success", "message": f"Stopped logging for {interface}."}), 200

def can_shutdown(request):
    """
    Shuts down the specified CAN interface(s).
    """
    global bus_can0, bus_can1  # Odwołanie do zmiennych globalnych
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    interfaces = data.get("interfaces")  # Lista interfejsów do wyłączenia

    # Walidacja wejścia
    if not isinstance(interfaces, list) or not all(iface in ["can0", "can1"] for iface in interfaces):
        return jsonify({"status": "error", "message": "Invalid interfaces. Must be a list containing 'can0' and/or 'can1'."}), 400

    shutdown_status = {}

    try:
        if "can0" in interfaces:
            if 'bus_can0' in globals() and bus_can0:
                bus_can0.shutdown()
                bus_can0 = None
                shutdown_status["can0"] = "shutdown"
            else:
                shutdown_status["can0"] = "not initialized"

        if "can1" in interfaces:
            if 'bus_can1' in globals() and bus_can1:
                bus_can1.shutdown()
                bus_can1 = None
                shutdown_status["can1"] = "shutdown"
            else:
                shutdown_status["can1"] = "not initialized"

        return jsonify({
            "status": "success",
            "message": "CAN interface(s) shutdown process completed.",
            "details": shutdown_status
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to shut down CAN interface(s): {str(e)}"
        }), 500