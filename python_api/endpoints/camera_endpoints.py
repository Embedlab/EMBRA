from flask import Blueprint, request, jsonify, send_from_directory
import modules.camera_module as camera_module

bp = Blueprint('camera', __name__, url_prefix='/CAMERA')

@bp.route('/STATUS', methods=['GET'])
def camera_status():
    """
    Returns the current status of the camera.
    """
    return camera_module.camera_status()

@bp.route('/RECORD', methods=['GET'])
def start_recording(dir="/home/pi/video"):
    """
    Starts video recording.
    """
    return camera_module.start_recording()

@bp.route('/STOP', methods=['GET'])
def stop_recording():
    """
    Stops video recording.
    """
    return camera_module.stop_recording()

@bp.route('/PHOTO', methods=['GET'])
def capture_photo():
    """
    Captures a photo using the camera and saves it to the specified directory.
    """
    return camera_module.capture_photo()

@bp.route('/')
def camera_ui():
    return send_from_directory('static/CAMERA', 'camera.html')
    