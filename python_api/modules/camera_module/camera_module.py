from picamera2 import MappedArray, Picamera2
from picamera2.encoders import H264Encoder
import time
import board
import os
from datetime import datetime
from flask import Flask, request, jsonify
from threading import Thread

picam2 = None
encoder = None
camera_flag = False

def camera_status():
    """
    Returns the current status of the camera.
    """
    if camera_flag:
        return jsonify({"status": "success", "message": "Camera is busy."}), 200
    return jsonify({"status": "success", "message": "Camera is ready."}), 200

def start_recording_logic(dir="/home/pi/video"):
    """
    Starts video recording. Handles logic independently of Flask.
    """
    global picam2, encoder, camera_flag

    if camera_flag:
        return {"status": "failed", "message": "Camera is busy."}, 400

    if not os.path.exists(dir):
        os.makedirs(dir)

    if picam2 is None:
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080)}))
        encoder = H264Encoder(10000000)

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    video_filename = f"video_{timestamp}.h264"
    picam2.start_recording(encoder, os.path.join(dir, video_filename))
    camera_flag = True

    return {"status": "success", "message": "Started recording video."}, 200

def start_recording():
    response, status_code = start_recording_logic()
    return jsonify(response), status_code

def stop_recording():
    """
    Stops video recording.
    """
    global camera_flag

    if picam2:
        picam2.stop_recording()
        camera_flag = False
        return jsonify({"status": "success", "message": "Stopped recording video."}), 200
    return jsonify({"status": "error", "message": "Camera not initialized."}), 400

def capture_photo():
    """
    Captures a photo using the camera and saves it to the specified directory.
    """
    global picam2, camera_flag

    # Prevent capturing a photo while the camera is recording
    if camera_flag:
        return jsonify({"status": "failed", "message": "Camera is busy."}), 400

    # Extract directory from the request or use default
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
    dir = data.get("dir", "/home/pi/photos")

    if not os.path.exists(dir):
        os.makedirs(dir)

    if picam2 is None:
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration(main={"size": (1920, 1080)}))

    # Start and capture photo
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    photo_filename = f"photo_{timestamp}.jpg"
    picam2.start()
    time.sleep(1)  # Allow the camera to stabilize
    picam2.capture_file(os.path.join(dir, photo_filename))
    picam2.stop()

    return jsonify({
        "status": "success",
        "message": "Photo captured successfully.",
        "file": os.path.join(dir, photo_filename)
    }), 200
    