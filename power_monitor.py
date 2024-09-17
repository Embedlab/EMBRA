import time
import board
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
import os
import argparse

def clear_terminal():
    # Clear the terminal screen using ANSI escape codes
    os.system('clear')

# Function to print data for a specific channel
def print_channel_data(channel, ina):
    bus_voltage = ina.bus_voltage        # voltage on V- (load side)
    shunt_voltage = ina.shunt_voltage    # voltage between V+ and V- across the shunt
    power = ina.power
    current = ina.current                # current in mA

    print(f"Channel {channel}:")
    print("PSU Voltage:{:6.3f}V    Shunt Voltage:{:9.6f}V    Load Voltage:{:6.3f}V    Power:{:9.6f}W    Current:{:9.6f}A".format(
        (bus_voltage + shunt_voltage), shunt_voltage, bus_voltage, power, current / 1000))


# Argument parsing
parser = argparse.ArgumentParser(description="Display data for specific INA219 channel.")
parser.add_argument('channel', nargs='?', choices=['CH1', 'CH2', 'CH3'], help="Specify which channel to display (CH1, CH2, CH3). If not provided, all channels will be shown.")
args = parser.parse_args()

# I2C setup
i2c_bus = board.I2C()

ina1 = INA219(i2c_bus, addr=0x40)
ina2 = INA219(i2c_bus, addr=0x41)
ina3 = INA219(i2c_bus, addr=0x42)

ina1.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina1.bus_voltage_range = BusVoltageRange.RANGE_16V

ina2.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2.bus_voltage_range = BusVoltageRange.RANGE_16V

ina3.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina3.bus_voltage_range = BusVoltageRange.RANGE_16V

try:
    # Measure and display loop
    while True:
        # Clear the terminal at the start of each iteration
        clear_terminal()

        # Display data for the specified channel, or all if no channel is specified
        if args.channel == 'CH1':
            print_channel_data(1, ina1)
        elif args.channel == 'CH2':
            print_channel_data(2, ina2)
        elif args.channel == 'CH3':
            print_channel_data(3, ina3)
        else:
            # Display data for all channels
            print_channel_data(1, ina1)
            print_channel_data(2, ina2)
            print_channel_data(3, ina3)

        # Pause for 1 second
        time.sleep(1)

except KeyboardInterrupt:
    # Gracefully exit the program when Ctrl+C is pressed
    print("\nExiting...")
