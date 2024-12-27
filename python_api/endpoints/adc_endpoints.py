from flask import Blueprint, request, jsonify, send_from_directory
import modules.ina219_module as ina219_module

bp = Blueprint('adc', __name__, url_prefix='/ADC')

@bp.route('/INITIALIZE', methods=['POST'])
def initialize_adc():
    """
    Initializes ADC sensors.
    """
    return ina219_module.initialize_adc(request)

@bp.route('/STATUS', methods=['GET'])
def adc_status():
    """
    Returns the current status of ADC sensors.
    """
    return ina219_module.ina219_status()

@bp.route('/READ', methods=['GET'])
def adc_read():
    """
    Reads the current data from the ADC sensors.
    """
    return ina219_module.ina219_read()

@bp.route('/LOG', methods=['POST'])
def adc_log():
    """
    Logs the data from the ADC sensors.
    """
    return ina219_module.ina219_log_data(request)

@bp.route('/SHUTDOWN', methods=['POST'])
def adc_shutdown():
    """
    Shutdown the ADC sensor.
    """
    return ina219_module.ina219_shutdown(request)

@bp.route('/')
def adc_ui():
    return send_from_directory("static/ADC", "adc.html")
    