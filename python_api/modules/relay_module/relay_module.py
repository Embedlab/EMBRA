from flask import Flask, request, jsonify, render_template_string
import os

relay_states = {
    "CH1": "OFF",
    "CH2": "OFF",
    "CH3": "OFF"
}

relay_gpio_map = {
    "CH1": 538,
    "CH2": 532,
    "CH3": 533
}

def set_relay(request):
    """
    Sets the relay state by writing to the GPIO interface.
    
    Parameters:
        channel (str): The relay channel ('CH1', 'CH2', or 'CH3').
        state (str): The desired state ('ON' or 'OFF').
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON data."}), 400

        channel = data.get("channel")
        channel = f"CH{channel}"

        if channel is None:
                return jsonify({"status": "error", "message": "Channel ID is required."}), 400

        if channel not in relay_gpio_map:
            return jsonify({"status": "error", "message": "Invalid relay interface. Use '1', '2' or '3'."}), 400

        if relay_states[channel] == "ON":
            state = "OFF"
        elif relay_states[channel] == "OFF":
            state = "ON"
        
        if state not in ["ON", "OFF"]:
            raise ValueError(f"Invalid state: {state}. Valid states: ON, OFF.")
        
        gpio_pin = relay_gpio_map[channel]
        gpio_state = 0 if state == "ON" else 1  # ON=0, OFF=1
        
        # Unexport the GPIO if already exported
        if os.path.exists(f"/sys/class/gpio/gpio{gpio_pin}"):
            with open("/sys/class/gpio/unexport", "w") as f:
                f.write(str(gpio_pin))
        
        # Export the GPIO pin
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(gpio_pin))
        
        # Set the direction and state
        with open(f"/sys/class/gpio/gpio{gpio_pin}/direction", "w") as f:
            f.write("out")
        with open(f"/sys/class/gpio/gpio{gpio_pin}/value", "w") as f:
            f.write(str(gpio_state))
        
        # Update the relay state for logging/debugging
        relay_states[channel] = state
        print(f"Relay {channel} {state}")
        return jsonify({"status": "success", "message": f"Relay {channel} toggled to {state}."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_relay_status():
    """
    Returns the current status of all relays.
    """
    return jsonify({"status": "success", "data": relay_states}), 200
