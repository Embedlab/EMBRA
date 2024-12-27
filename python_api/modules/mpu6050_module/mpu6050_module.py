from mpu6050 import mpu6050
from flask import Flask, request, jsonify, render_template_string
import csv
from datetime import datetime
import os
from threading import Thread

mpu = None
initialized = False
logging_thread = None
logging_active = False

def mpu6050_initialize():

    global mpu, initialized

    mpu = mpu6050(0x68)
    initialized = True
    return jsonify({"status": "success", "messege": "MPU6050 initialized"}), 200

def mpu6050_status():

    global mpu, logging_active

    if mpu is None:
        return jsonify({"status": "failure", "state": "not initialized"}), 400
    try:
        if logging_active:
            return jsonify({"status": "success", "state": "MPU6050 is busy logging"}), 200
        elif mpu.get_accel_data():
            return jsonify({"status": "success", "state": "initialized"}), 200
    except Exception as e:
        return jsonify({"status": "failure", "error": str(e)}), 500

def mpu6050_read():

    global initialized

    if initialized:
        return jsonify({"status": "success", "state": "initialised", "data": {"accel": mpu.get_accel_data(), "gyro": mpu.get_gyro_data(), "temp": mpu.get_temp()}}), 200
    else:
        return jsonify({"status": "success", "state": "not initialized"}), 200

def mpu6050_log_data():

    global logging_active
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csv_dir = "/home/pi/mpu6050"

    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    csv_files = {
        "mpu": open(os.path.join(csv_dir, f"mpu6050_{timestamp}.csv"), mode='a', newline='')
    }

    csv_writers = {
        "mpu": csv.DictWriter(csv_files["mpu"], fieldnames=['Timestamp', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Temperature'])
    }

    for channel, file in csv_files.items():
        if os.stat(file.name).st_size == 0:
            csv_writers[channel].writeheader()

    try:
        while logging_active:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

    finally:
        for file in csv_files.values():
            file.close()

def mpu6050_log(request):

    global logging_thread, logging_active, initialized

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON data."}), 400
    
    if not initialized:
        return jsonify({"status": "success", "state": "MPU6050 not initialized"}), 200

    action = data.get("action")

    if action == "start":
        if logging_active:
            return jsonify({"status": "error", "message": f"Logging is already active for ."}), 400

        logging_active = True
        thread = Thread(target=mpu6050_log_data, args=(), daemon=True)
        logging_thread = thread
        thread.start()
        return jsonify({"status": "success", "message": f"Started logging for MPU6050."}), 200

    elif action == "stop":
        if not logging_active:
            return jsonify({"status": "error", "message": f"Logging is not active for MPU6050."}), 400

        logging_active = False
        logging_thread.join()  # Wait for thread to finish
        return jsonify({"status": "success", "message": f"Stopped logging for MPU6050."}), 200

def mpu6050_shutdown():
    global mpu, initialized, logging_active, logging_thread

    if initialized:
        # Stop logging if active
        logging_active = False
        if logging_thread is not None:
            logging_thread.join()
            logging_thread = None

        # Deinitialize sensor by resetting the MPU object
        mpu = None
        initialized = False

        return jsonify({"status": "success", "message": "MPU6050 sensor deinitialized and shutdown."}), 200
    else:
        return jsonify({"status": "error", "message": "MPU6050 is not initialized."}), 400