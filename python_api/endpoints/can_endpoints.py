from flask import Blueprint, request, jsonify, send_from_directory
import modules.can_module as can_module

bp = Blueprint('can', __name__, url_prefix='/CAN')

@bp.route('/INITIALIZE', methods=['POST'])
def initialize_can():
    """
    Initializes the specified CAN bus (can0 or can1).
    """
    return can_module.initialize_can(request)

@bp.route('/STATUS', methods=['GET'])
def can_status():
    """
    Returns the status of CAN interfaces (can0 and can1).
    """
    return can_module.can_status()

@bp.route('/SEND', methods=['POST'])
def can_send():
    """
    Sends a CAN message to the specified CAN interface.
    """
    return can_module.can_send(request)

@bp.route('/LOG', methods=['POST'])
def log_can():
    """
    Starts or stops CAN logging for the specified interface.
    """
    return can_module.log_can(request)

@bp.route('/SHUTDOWN', methods=['POST'])
def can_shutdown():
    """
    Shuts down the specified CAN interface(s).
    """
    return can_module.can_shutdown(request)

@bp.route('/')
def can_ui():
    return send_from_directory('static/CAN', 'can.html')
    
