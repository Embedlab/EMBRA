from flask import Blueprint, request, jsonify, send_from_directory
import modules.relay_module as relay_module

bp = Blueprint('relay', __name__, url_prefix='/RELAY')

@bp.route('/STATUS', methods=['GET'])
def relay_status():
    """
    Returns the current status of all relays.
    """
    return relay_module.get_relay_status()

@bp.route('/TOGGLE', methods=['POST'])
def toggle_relay():
    """
    Toggles the state of a relay (ON/OFF).
    """
    return relay_module.set_relay(request)

@bp.route('/')
def relay_ui():
    return send_from_directory('static/RELAY', 'relay.html')
    