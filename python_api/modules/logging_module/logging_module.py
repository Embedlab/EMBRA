from flask import Flask, request, jsonify
from flask import current_app as app
from threading import Thread
import os
import csv
import board
import time
from datetime import datetime
import can
from mpu6050 import mpu6050
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
import cv2

import modules.camera_module as camera_module

mpu = mpu6050(0x68)

i2c_bus = board.I2C()
ina1 = INA219(i2c_bus, addr=0x40)
ina2 = INA219(i2c_bus, addr=0x41)
ina3 = INA219(i2c_bus, addr=0x42)

ina1.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.bus_voltage_range = BusVoltageRange.RANGE_16V


ina2.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.bus_voltage_range = BusVoltageRange.RANGE_16V


ina3.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.bus_voltage_range = BusVoltageRange.RANGE_16V

collecting_data = False
logging_thread = None

def collect_data(data):
    """
    Collects data based on enabled options and writes to CSV files.
    """
    global collecting_data

    csv_files = {}
    csv_writers = {}

    options = {
        "camera": data.get("camera", False),
        "adc1": data.get("adc1", False),
        "adc2": data.get("adc2", False),
        "adc3": data.get("adc3", False),
        "mpu6050": data.get("mpu6050", False),
        "can0": data.get("can0", False),
        "can1": data.get("can1", False)
    }

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    csv_dir = f"/home/pi/logs/session_{timestamp}"

    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    try:
        # Initialize CSV files and writers
        if options["adc1"] == "True":
            csv_files[1] = open(os.path.join(csv_dir, "adc_1.csv"), mode='a', newline='')
            csv_writers[1] = csv.DictWriter(csv_files[1], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current'])
            if os.stat(csv_files[1].name).st_size == 0:
                csv_writers[1].writeheader()

        if options["adc2"] == "True":
            csv_files[2] = open(os.path.join(csv_dir, "adc_2.csv"), mode='a', newline='')
            csv_writers[2] = csv.DictWriter(csv_files[2], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current'])
            if os.stat(csv_files[2].name).st_size == 0:
                csv_writers[2].writeheader()

        if options["adc3"] == "True":
            csv_files[3] = open(os.path.join(csv_dir, "adc_3.csv"), mode='a', newline='')
            csv_writers[3] = csv.DictWriter(csv_files[3], fieldnames=['Timestamp', 'PSU Voltage', 'Shunt Voltage', 'Load Voltage', 'Power', 'Current'])
            if os.stat(csv_files[3].name).st_size == 0:
                csv_writers[3].writeheader()

        if options["mpu6050"] == "True":
            csv_files["mpu"] = open(os.path.join(csv_dir, "mpu6050.csv"), mode='a', newline='')
            csv_writers["mpu"] = csv.DictWriter(csv_files["mpu"], fieldnames=['Timestamp', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temperature'])
            if os.stat(csv_files["mpu"].name).st_size == 0:
                csv_writers["mpu"].writeheader()

        if options["can0"] == "True":
            file_path = os.path.join(csv_dir, "can0.csv")
            csv_files["can0"] = open(file_path, mode='a', newline='')
            csv_writers["can0"] = csv.DictWriter(csv_files["can0"], fieldnames=['Timestamp', 'CAN ID', 'Data'])
            if os.path.getsize(file_path) == 0:
                csv_writers["can0"].writeheader()
                csv_files["can0"].flush()

        if options["can1"] == "True":
            file_path = os.path.join(csv_dir, "can1.csv")
            csv_files["can1"] = open(file_path, mode='a', newline='')
            csv_writers["can1"] = csv.DictWriter(csv_files["can1"], fieldnames=['Timestamp', 'CAN ID', 'Data'])
            if os.path.getsize(file_path) == 0:
                csv_writers["can1"].writeheader()
                csv_files["can1"].flush()

        # Initialize CAN buses
        bus_can0 = can.interface.Bus(channel='can0', interface='socketcan') if options["can0"] else None
        bus_can1 = can.interface.Bus(channel='can1', interface='socketcan') if options["can1"] else None

        # Data collection loop
        while collecting_data:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if options["camera"] == "True":
                camera_module.start_recording_logic(csv_dir)


            if options["adc1"] == "True":
                bus_voltage = ina1.bus_voltage
                shunt_voltage = ina1.shunt_voltage
                power = ina1.power
                current = ina1.current

                data = {
                    'Timestamp': timestamp,
                    'PSU Voltage': bus_voltage + shunt_voltage,
                    'Shunt Voltage': shunt_voltage,
                    'Load Voltage': bus_voltage,
                    'Power': power,
                    'Current': current / 1000
                }
                csv_writers[1].writerow(data)

            if options["adc2"] == "True":
                bus_voltage = ina2.bus_voltage
                shunt_voltage = ina2.shunt_voltage
                power = ina2.power
                current = ina2.current

                data = {
                    'Timestamp': timestamp,
                    'PSU Voltage': bus_voltage + shunt_voltage,
                    'Shunt Voltage': shunt_voltage,
                    'Load Voltage': bus_voltage,
                    'Power': power,
                    'Current': current / 1000
                }
                csv_writers[2].writerow(data)

            if options["adc3"] == "True":
                bus_voltage = ina3.bus_voltage
                shunt_voltage = ina3.shunt_voltage
                power = ina3.power
                current = ina3.current

                data = {
                    'Timestamp': timestamp,
                    'PSU Voltage': bus_voltage + shunt_voltage,
                    'Shunt Voltage': shunt_voltage,
                    'Load Voltage': bus_voltage,
                    'Power': power,
                    'Current': current / 1000
                }
                csv_writers[3].writerow(data)

            if options["mpu6050"] == "True":
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

            if options["can0"] == "True":
                try:
                    message = bus_can0.recv(timeout=0.01)
                    if message:
                        can_data = {
                            'Timestamp': timestamp, 
                            'CAN ID': hex(message.arbitration_id), 
                            'Data': message.data.hex() if message.data else 'No Data'}
                        csv_writers["can0"].writerow(can_data)
                        csv_files["can0"].flush()
                except can.CanError:
                    pass

            if options["can1"] == "True":
                try:
                    message = bus_can1.recv(timeout=0.01)
                    if message:
                        can_data = {
                            'Timestamp': timestamp, 
                            'CAN ID': hex(message.arbitration_id), 
                            'Data': message.data.hex() if message.data else 'No Data'}
                        csv_writers["can1"].writerow(can_data)
                        csv_files["can1"].flush()
                except can.CanError:
                    pass
                    
    finally:
        # Cleanup
        if bus_can0:
            bus_can0.shutdown()
        if bus_can1:
            bus_can1.shutdown()
        for file in csv_files.values():
            file.close()

def start_logging(request):
    """
    Starts logging data based on the input JSON.
    """
    global collecting_data, logging_thread

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

    if collecting_data:
        return jsonify({"status": "error", "message": "Logging is already active."}), 400

    collecting_data = True

    logging_thread = Thread(target=collect_data, args=(data,), daemon=True)
    logging_thread.start()

    return jsonify({"status": "success", "message": "Logging started."}), 200

def logging_status():
    """
    Returns logging status.
    """
    if collecting_data == True:
        message = "active"
    else:
        message = "inactive"
    return jsonify({"status": "success", "message": f"Logging is {message}."}), 200

def stop_logging():
    """
    Stops logging data.
    """
    global collecting_data, picam2
    collecting_data = False

    # if picam2 is not None:
    #     picam2.stop_recording()
    camera_module.stop_recording()

    return jsonify({"status": "success", "message": "Stopped logging."}), 200


def apply_timestamp(request):
    """
    Add a timestamp to each video frame.
    """
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
