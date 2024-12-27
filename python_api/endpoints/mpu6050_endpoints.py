from flask import Blueprint, request, jsonify
import modules.mpu6050_module as mpu6050_module

bp = Blueprint('mpu6050', __name__, url_prefix='/MPU6050')

@bp.route('/INITIALIZE', methods=['GET'])
def initialize_mpu6050():
    """
    Initializes the MPU6050 sensor.
    """
    return mpu6050_module.mpu6050_initialize()

@bp.route('/STATUS', methods=['GET'])
def mpu6050_status():
    """
    Returns the current status of MPU6050 sensor.
    """
    return mpu6050_module.mpu6050_status()

@bp.route('/READ', methods=['GET'])
def mpu6050_read():
    """
    Reads data from the MPU6050 sensor.
    """
    return mpu6050_module.mpu6050_read()

@bp.route('/LOG', methods=['POST'])
def mpu6050_log():
    """
    Logs data from the MPU6050 sensor.
    """
    return mpu6050_module.mpu6050_log(request)

@bp.route('/SHUTDOWN', methods=['GET'])
def mpu6050_shutdown():
    """
    Shutdown the MPU6050 sensor.
    """
    return mpu6050_module.mpu6050_shutdown()
    