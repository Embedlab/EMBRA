from flask import Blueprint, request, jsonify
import modules.utils_module as utils_module

bp = Blueprint('utils', __name__, url_prefix='')

@bp.route('/SESSIONS/DELETE', methods=['GET'])
def delete_sessions():
    """
    Deletes all sessions.
    """
    return utils_module.delete_sessions()

@bp.route('/SESSIONS/GET', methods=['GET'])
def get_sessions():
    """
    Retrieves all sessions.
    """
    return utils_module.get_sessions()

@bp.route('/SESSIONS/EXPORT', methods=['GET'])
def export_log():
    """
    Exports logs from the specified folder as a zip file.
    The folder path is provided in the JSON payload with key 'folder'.
    """
    return utils_module.export_log()

@bp.route('/ENDPOINTS', methods=['GET'])
def list_endpoints():
    """
    Lists all available endpoints with their methods.
    """
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            "endpoint": rule.endpoint,
            "url": str(rule),
            "methods": list(rule.methods)
        })
    return jsonify({"status": "success", "endpoints": endpoints}), 200
