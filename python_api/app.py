from flask import Flask
from endpoints import can_endpoints, relay_endpoints, mpu6050_endpoints, adc_endpoints, camera_endpoints, logging_endpoints, utils_endpoints

app = Flask(__name__)

app.register_blueprint(can_endpoints.bp)
app.register_blueprint(relay_endpoints.bp)
app.register_blueprint(mpu6050_endpoints.bp)
app.register_blueprint(adc_endpoints.bp)
app.register_blueprint(camera_endpoints.bp)
app.register_blueprint(logging_endpoints.bp)
app.register_blueprint(utils_endpoints.bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
