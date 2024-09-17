#!/bin/bash

# Display usage information
usage() {
    echo "Usage: $0 [CH1|CH2|CH3]"
    echo ""
    echo "Options:"
    echo "  CH1          Display data for INA219 channel 1"
    echo "  CH2          Display data for INA219 channel 2"
    echo "  CH3          Display data for INA219 channel 3"
    echo "  (no argument) Display data for all channels"
    echo "  -h, --help   Display this help message"
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

# Validate argument if provided
if [[ "$1" != "" && "$1" != "CH1" && "$1" != "CH2" && "$1" != "CH3" ]]; then
    echo "Error: Invalid argument '$1'"
    usage
    exit 1
fi

# Run the Python script with the provided argument (or no argument for all channels)
if [[ "$1" != "" ]]; then
    python3 /home/$USER/.power_monitor.py "$1"
else
    python3 /home/$USER/.power_monitor.py
fi
