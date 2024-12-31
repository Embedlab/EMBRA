from flask import Blueprint, request, jsonify, send_from_directory
import modules.logging_module as logging_module

bp = Blueprint('logging', __name__, url_prefix='/LOGGING')

@bp.route('/STATUS', methods=['GET'])
def logging_status():
    """
    Returns logging status.
    """
    return logging_module.logging_status()

@bp.route('/START', methods=['POST'])
def start_logging():
    """
    Starts logging data.
    """
    return logging_module.start_logging(request)

@bp.route('/STOP', methods=['GET'])
def stop_logging():
    """
    Stops logging data.
    """
    return logging_module.stop_logging()

@bp.route('/')
def logging_ui():
    return send_from_directory('static/LOGGING', 'logging.html')
    