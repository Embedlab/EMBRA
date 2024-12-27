from flask import Flask, jsonify, send_from_directory
from endpoints import can_endpoints, relay_endpoints, mpu6050_endpoints, adc_endpoints, camera_endpoints, logging_endpoints, utils_endpoints

app = Flask(__name__, static_folder='static')

app.register_blueprint(can_endpoints.bp)
app.register_blueprint(relay_endpoints.bp)
app.register_blueprint(mpu6050_endpoints.bp)
app.register_blueprint(adc_endpoints.bp)
app.register_blueprint(camera_endpoints.bp)
app.register_blueprint(logging_endpoints.bp)
app.register_blueprint(utils_endpoints.bp)

@app.route('/ENDPOINTS', methods=['GET'])
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

@app.route('/')
def ui():
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
