from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
from flask import Flask, request, jsonify
import time
from datetime import datetime
import csv
import board
import os
from threading import Thread

# Setup the I2C bus and sensors
i2c_bus = board.I2C()
ina1 = None
ina2 = None
ina3 = None

adc_states = {
    "1": "OFF",
    "2": "OFF",
    "3": "OFF"
}

logging_adc_active = {
    "1": False, 
    "2": False,
    "3": False
}

collecting_data = False
logging_threads = {}

def initialize_adc(request):
    """
    Initializes ADC sensors.
    """
    global ina1, ina2, ina3

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    channel = data.get("channel")
    
    if channel not in adc_states:
        return jsonify({"status": "error", "message": "Invalid ADC channel. Use '1', '2' or '3'."}), 400

    try:
        if channel == "1" and ina1 is None:
            ina1 = INA219(i2c_bus, addr=0x40)

            ina1.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina1.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina1.bus_voltage_range = BusVoltageRange.RANGE_16V
            adc_states[channel] = "ON" 
        elif channel == "2" and ina2 is None:
            ina2 = INA219(i2c_bus, addr=0x41)

            ina2.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina2.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina2.bus_voltage_range = BusVoltageRange.RANGE_16V
            adc_states[channel] = "ON"
        elif channel == "3" and ina3 is None:
            ina3 = INA219(i2c_bus, addr=0x42)

            ina3.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina3.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina3.bus_voltage_range = BusVoltageRange.RANGE_16V
            adc_states[channel] = "ON"
        return jsonify({"status": "success", "message": f"channel {channel} initialized."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def ina219_status():
    global adc_states
    return jsonify({"status": "success", "channel": adc_states}), 200

def ina219_read():
    """
    Reads the current data from the ADC sensors.
    """

    global adc_states, ina1, ina2, ina3, logging_adc_active

    data = {}

    try:
        if ina1 is not None:
            data["1"] = {
                "bus_voltage": ina1.bus_voltage,
                "shunt_voltage": ina1.shunt_voltage,
                "current": ina1.current
            }
        else:
            data["1"] = "Not initialized"

        if ina2 is not None:
            data["2"] = {
                "bus_voltage": ina2.bus_voltage,
                "shunt_voltage": ina2.shunt_voltage,
                "current": ina2.current
            }
        else:
            data["2"] = "Not initialized"

        if ina3 is not None:
            data["3"] = {
                "bus_voltage": ina3.bus_voltage,
                "shunt_voltage": ina3.shunt_voltage,
                "current": ina3.current
            }
        else:
            data["3"] = "Not initialized"

        return jsonify({"status": "success", "channel": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to read INA219 data: {str(e)}"}), 500

def ina219_log(channel):
    global collecting_data, logging_adc_active

    csv_dir = "/home/pi/ADC"

    if channel == "1":
        interface = ina1
    elif channel == "2":
        interface = ina2
    elif channel == "3":
        interface = ina3

    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    csv_files = {
        channel: open(os.path.join(csv_dir, f"CH_{channel}_{timestamp}.csv"), mode='a', newline=''),
    }

    csv_writers = {
        channel: csv.DictWriter(csv_files[channel], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current']),
    }

    for channel, file in csv_files.items():
        if os.stat(file.name).st_size == 0:
            csv_writers[channel].writeheader()

    try:
        while logging_adc_active[channel]:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for channel, ina in [(channel, interface)]:
                bus_voltage = ina.bus_voltage
                shunt_voltage = ina.shunt_voltage
                power = ina.power
                current = ina.current

                data = {
                    'Timestamp': timestamp,
                    'PSU Voltage': bus_voltage + shunt_voltage,
                    'Shunt Voltage': shunt_voltage,
                    'Load Voltage': bus_voltage,
                    'Power': power,
                    'Current': current / 1000
                }
                csv_writers[channel].writerow(data)

    finally:
        for file in csv_files.values():
            file.close()

def ina219_log_data(request):
    """
    Starts or stops ADC logging for the specified channel.
    """
    global collect_data, adc_states, logging_threads

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    channel = data.get("channel")
    action = data.get("action")

    if channel not in ["1", "2", "3"]:
       return jsonify({"status": "error", "message": "Invalid ADC channel. Use '1', '2' or '3'."}), 400
    if action not in ["start", "stop"]:
        return jsonify({"status": "error", "message": "Invalid action. Use 'start' or 'stop'."}), 400

    if adc_states[channel] == "OFF":
        return jsonify({"status": "success", "state": "MPU6050 not initialized"}), 200

    if action == "start":
        if logging_adc_active[channel]:
            return jsonify({"status": "error", "message": f"Logging is already active for CH{channel}."}), 400

        logging_adc_active[channel] = True
        thread = Thread(target=ina219_log, args=(channel,), daemon=True)
        logging_threads[channel] = thread
        thread.start()
        return jsonify({"status": "success", "message": f"Started logging for CH{channel}."}), 200

    elif action == "stop":
        if not logging_adc_active[channel]:
            return jsonify({"status": "error", "message": f"Logging is not active for CH{channel}."}), 400

        logging_adc_active[channel] = False
        logging_threads[channel].join()
        return jsonify({"status": "success", "message": f"Stopped logging for CH{channel}."}), 200

def ina219_shutdown(request):
    global ina1, ina2, ina3, logging_adc_active, logging_thread, adc_states

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    channel = data.get("channel")

    if channel not in ["1", "2", "3"]:
        return jsonify({"status": "error", "message": "Invalid ADC channel. Use '1', '2' or '3'."}), 400

    if adc_states.get(channel) == "OFF":
        return jsonify({"status": "error", "message": f"ADC channel {channel} not initialized"}), 400

    if logging_adc_active.get(channel):
        logging_adc_active[channel] = False
        if logging_threads[channel] is not None:
            logging_threads[channel].join()
            logging_threads[channel] = None

    if channel == "1":
        ina1 = None
    elif channel == "2":
        ina2 = None
    elif channel == "3":
        ina3 = None
    
    adc_states[channel] = "OFF"

    return jsonify({"status": "success", "message": f"INA219 channel {channel} deinitialized and shutdown."}), 200
