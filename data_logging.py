import time
import board
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
import os
import csv
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from threading import Thread
import can
from mpu6050 import mpu6050
import cv2
from picamera2 import MappedArray, Picamera2
from picamera2.encoders import H264Encoder
import zipfile

app = Flask(__name__)

# Global variables for Picamera2
picam2 = None
encoder = None

relay_states = {
    "CH1": "OFF",
    "CH2": "OFF",
    "CH3": "OFF"
}

# GPIO mapping for relays
relay_gpio_map = {
    "CH1": 538,
    "CH2": 532,
    "CH3": 533
}

# Global variables to control data collection
collecting_data = False
csv_dir = "csv"

# Ensure the csv directory exists
if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

# Setup the I2C bus and sensors
i2c_bus = board.I2C()
ina1 = INA219(i2c_bus, addr=0x40)
ina2 = INA219(i2c_bus, addr=0x41)
ina3 = INA219(i2c_bus, addr=0x42)
mpu = mpu6050(0x68)

# Configure INA219 sensors
ina1.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.bus_voltage_range = BusVoltageRange.RANGE_16V

ina2.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.bus_voltage_range = BusVoltageRange.RANGE_16V

ina3.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.bus_voltage_range = BusVoltageRange.RANGE_16V

def collect_data():
    global collecting_data
    csv_files = {
        1: open(os.path.join(csv_dir, "channel_1.csv"), mode='a', newline=''),
        2: open(os.path.join(csv_dir, "channel_2.csv"), mode='a', newline=''),
        3: open(os.path.join(csv_dir, "channel_3.csv"), mode='a', newline=''),
        "can0": open(os.path.join(csv_dir, "can0.csv"), mode='a', newline=''),
        "can1": open(os.path.join(csv_dir, "can1.csv"), mode='a', newline=''),
        "mpu": open(os.path.join(csv_dir, "mpu6050.csv"), mode='a', newline='')
    }

    csv_writers = {
        1: csv.DictWriter(csv_files[1], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current']),
        2: csv.DictWriter(csv_files[2], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current']),
        3: csv.DictWriter(csv_files[3], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current']),
        "can0": csv.DictWriter(csv_files["can0"], fieldnames=['Timestamp', 'CAN ID', 'Data']),
        "can1": csv.DictWriter(csv_files["can1"], fieldnames=['Timestamp', 'CAN ID', 'Data']),
        "mpu": csv.DictWriter(csv_files["mpu"], fieldnames=['Timestamp', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temperature'])
    }

    for channel, file in csv_files.items():
        if os.stat(file.name).st_size == 0:
            csv_writers[channel].writeheader()

    bus_can0 = can.interface.Bus(channel='can0', interface='socketcan')
    bus_can1 = can.interface.Bus(channel='can1', interface='socketcan')

    try:
        while collecting_data:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for channel, ina in [(1, ina1), (2, ina2), (3, ina3)]:
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

            accel_data = mpu.get_accel_data()
            gyro_data = mpu.get_gyro_data()
            temperature = mpu.get_temp()

            mpu_data = {
                'Timestamp': timestamp,
                'Accel_X': accel_data['x'],
                'Accel_Y': accel_data['y'],
                'Accel_Z': accel_data['z'],
                'Gyro_X': gyro_data['x'],
                'Gyro_Y': gyro_data['y'],
                'Gyro_Z': gyro_data['z'],
                'Temperature': temperature
            }
            csv_writers["mpu"].writerow(mpu_data)

            for bus, channel_name in [(bus_can0, "can0"), (bus_can1, "can1")]:
                try:
                    message = bus.recv(timeout=0.01)
                    if message:
                        can_data = {
                            'Timestamp': timestamp,
                            'CAN ID': hex(message.arbitration_id),
                            'Data': message.data.hex() if message.data else 'No Data'
                        }
                        csv_writers[channel_name].writerow(can_data)
                except can.CanError:
                    continue

    finally:
        bus_can0.shutdown()
        bus_can1.shutdown()

        for file in csv_files.values():
            file.close()

def set_relay(channel, state):
    """
    Sets the relay state by writing to the GPIO interface.
    
    Parameters:
        channel (str): The relay channel ('CH1', 'CH2', or 'CH3').
        state (str): The desired state ('ON' or 'OFF').
    """
    if channel not in relay_gpio_map:
        raise ValueError(f"Invalid channel: {channel}. Valid channels: CH1, CH2, CH3.")
    
    if state not in ["ON", "OFF"]:
        raise ValueError(f"Invalid state: {state}. Valid states: ON, OFF.")
    
    gpio_pin = relay_gpio_map[channel]
    gpio_state = 0 if state == "ON" else 1  # ON=0, OFF=1
    
    # Unexport the GPIO if already exported
    if os.path.exists(f"/sys/class/gpio/gpio{gpio_pin}"):
        with open("/sys/class/gpio/unexport", "w") as f:
            f.write(str(gpio_pin))
    
    # Export the GPIO pin
    with open("/sys/class/gpio/export", "w") as f:
        f.write(str(gpio_pin))
    
    # Set the direction and state
    with open(f"/sys/class/gpio/gpio{gpio_pin}/direction", "w") as f:
        f.write("out")
    with open(f"/sys/class/gpio/gpio{gpio_pin}/value", "w") as f:
        f.write(str(gpio_state))
    
    # Update the relay state for logging/debugging
    relay_states[channel] = state
    print(f"Relay {channel} {state}")

def zip_csv_folder(folder_path, output_filename):
    """
    Function to zip all CSV files in a given folder.
    """
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".csv"):
                    zipf.write(os.path.join(root, file), arcname=file)

@app.route('/RELAY<relay_id>_<action>', methods=['GET'])
def control_relay(relay_id, action):
    """
    Controls the specified relay channel.
    
    URL Format:
        /RELAY1_ON
        /RELAY2_OFF
        /RELAY3_ON
    
    Parameters:
        relay_id (str): Relay channel ID (1, 2, or 3).
        action (str): Action to perform ('ON' or 'OFF').
    
    Returns:
        JSON response with status message.
    """
    channel = f"CH{relay_id}"
    action = action.upper()

    try:
        set_relay(channel, action)
        return jsonify({"status": "success", "message": f"Relay {channel} set to {action}"}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/DOWNLOAD_ZIP', methods=['GET'])
def download_zip():
    """
    Endpoint to zip all CSV files and allow downloading.
    """
    zip_filename = os.path.join(csv_dir, "csv_data.zip")
    
    # Zip all CSV files in the 'csv' directory
    zip_csv_folder(csv_dir, zip_filename)

    # Send the zip file for download
    return send_from_directory(csv_dir, "csv_data.zip", as_attachment=True)

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control Panel</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }
            button {
                margin: 10px;
                padding: 15px 30px;
                font-size: 16px;
                cursor: pointer;
            }
            .on { background-color: #4CAF50; color: white; }
            .off { background-color: #f44336; color: white; }
            .control { background-color: #008CBA; color: white; }
        </style>
    </head>
    <body>
        <h1>Control Panel</h1>
        
        <div>
            <h2>Data Collection</h2>
            <button class="control" onclick="sendRequest('START')">Start Data Collection</button>
            <button class="control" onclick="sendRequest('STOP')">Stop Data Collection</button>
        </div>
        
        <hr>

        <div>
            <h2>Relay Controls</h2>
            <div>
                <h3>Channel 1</h3>
                <button class="on" onclick="sendRequest('RELAY1_ON')">Turn ON</button>
                <button class="off" onclick="sendRequest('RELAY1_OFF')">Turn OFF</button>
            </div>
            <div>
                <h3>Channel 2</h3>
                <button class="on" onclick="sendRequest('RELAY2_ON')">Turn ON</button>
                <button class="off" onclick="sendRequest('RELAY2_OFF')">Turn OFF</button>
            </div>
            <div>
                <h3>Channel 3</h3>
                <button class="on" onclick="sendRequest('RELAY3_ON')">Turn ON</button>
                <button class="off" onclick="sendRequest('RELAY3_OFF')">Turn OFF</button>
            </div>
            <button class"on" onclick="downloadZip()">Download CSV Data as ZIP</button>
        </div>
        
        <script>
            function sendRequest(endpoint) {
                fetch(`/${endpoint}`)
                    .then(response => response.json())
                    .then(data => alert(data.message))
                    .catch(error => alert('Error: ' + error.message));
            }
            function downloadZip() {
                window.location.href = '/DOWNLOAD_ZIP';
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/START', methods=['GET'])
def start_collecting():
    """
    Endpoint to start data collection and recording video.
    """
    global collecting_data, picam2, encoder

    if not collecting_data:
        collecting_data = True

        # Start data collection in a separate thread
        thread = Thread(target=collect_data)
        thread.start()

        # Initialize Picamera2
        if picam2 is None:
            picam2 = Picamera2()
            picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080)}))
            picam2.pre_callback = apply_timestamp
            encoder = H264Encoder(10000000)

        # Start recording
        video_filename = f"video_{time.strftime('%Y%m%d_%H%M%S')}.h264"
        picam2.start_recording(encoder, os.path.join(csv_dir, video_filename))
        return jsonify({
            "status": "success",
            "message": "Started collecting data and recording video.",
            "video_file": video_filename,
            "collecting_data": collecting_data
        }), 200

    else:
        return jsonify({
            "status": "error",
            "message": "Data collection is already running.",
            "collecting_data": collecting_data
        }), 400


@app.route('/STOP', methods=['GET'])
def stop_collecting():
    """
    Endpoint to stop data collection and recording video.
    """
    global collecting_data, picam2

    if collecting_data:
        collecting_data = False

        # Stop recording video
        if picam2 is not None:
            picam2.stop_recording()

        return jsonify({
            "status": "success",
            "message": "Stopped collecting data and recording video.",
            "collecting_data": collecting_data
        }), 200

    else:
        return jsonify({
            "status": "error",
            "message": "Data collection is not running.",
            "collecting_data": collecting_data
        }), 400

def apply_timestamp(request):
    """
    Add a timestamp to each video frame.
    """
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
