# RemoteRover
A versatile platform for remote access and support, tailored for Raspberry Pi hardware. It automates the configuration of RPi OS, network interfaces, and communication protocols (SPI/I2C/Ethernet), while supporting extensions for power management and real-time monitoring. With optional camera integration, it offers live video streaming, making it perfect for seamless remote operations.

## Prerequisites

Before using this project, ensure the following prerequisites are met:

### 1. Linux or WSL (Windows Subsystem for Linux)
   - This script is designed to run on a Linux system. If you're using Windows, install and configure [WSL](https://docs.microsoft.com/en-us/windows/wsl/install) to run Linux commands.

### 2. Required Packages
   - Install the necessary packages by running the following commands:

   ```bash
   sudo apt update
   sudo apt install fdisk xz-utils sudo qemu-utils bc openssl coreutils grep sed systemd
   ```
   These packages are essential for handling the RPI image, mounting partitions, and automating configurations.

### 3. Raspberry Pi OS Image
   - Download the Raspberry Pi OS Lite image:
     - Go to the official Raspberry Pi website: [Raspberry Pi OS](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-32-bit)
     - Choose and download the **Raspberry Pi OS Lite** version (32-bit).
   - This image is a minimal version, providing a lightweight OS suitable for headless setups.


## Basic Usage

1. **Download the repository**  
   Clone or download the repository to your local machine.

2. **Copy and configure the RPi OS Image**  
   - Copy the Raspberry Pi OS image into the repository folder.
   - Set the `IMGXZ` variable in the `env` file to the full name of the image file.

3. **Configure host, user, and login details**  
   Edit the `env` file with your specific information:
   - Set `RASPIHOST` to name the host.
   - Set `USERNAME` to define the user.
   - Set `USERPASS` to define the password for the user.

4. **Configure network settings**  
   a. **Static Ethernet network configuration**  
      - Set `RUN_ETH=1` to configure Ethernet with a static IP.
      - Set `NETIP` to the static IP address.
      - Set `NETMASK` to the appropriate subnet mask.
      - Set `NETGW` to the default gateway.
   
   b. **Static or dynamic WLAN network configuration**  
      - Set `RUN_WLAN_DHCP=1` to use DHCP for Wi-Fi.  
      OR  
      - Set `RUN_WLAN=1` to configure Wi-Fi with a static IP.
      - Set `SSID` to the name of the Wi-Fi network.
      - Set `PSK` to the Wi-Fi network password.
      - If using static IP addresses:
        - Set `WLAN_NETIP` to the desired IP address.
        - Set `WLAN_NETMASK` to the subnet mask.
        - Set `WLAN_NETGW` to the default gateway.

5. **Configure features for the image**  
   In the `env` file, enable the required features by setting the corresponding `RUN_*` variables:
   - Set `RUN_I2C=1` to enable I2C.
   - Set `RUN_SPI=1` to enable SPI.
   - Set `RUN_SERIAL=1` to enable UART.
   - Set `RUN_STM32=1` to enable the STM32 GDB server.
   - Set `RUN_CAMERA=1` to enable the Raspberry Pi Camera.
   - Set `RUN_CURRENT_MONITOR=1` to enable the Power Monitor HAT.
   - Set `RUN_RELAY=1` to enable the Waveshare Raspberry Pi Relay Board.

6. **Generate the image**  
   Run the following command to generate the custom Raspberry Pi OS image:

   ```bash
   sudo ./remoterover.sh
   ```

7. **Write the generated image to an SD Card**
   - Download and use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write the generated image to an SD card.
   - Select "Use custom" when choosing the image to write, and select the generated image.


## Using extra default interfaces:
Make sure `RUN_I2C` and/or `RUN_SPI` are enabled if you want those interfaces to be auto-configured.

### I²C (I2C, IIC)
Use `i2cdetect -y 1` to scan for external I2C devices.

`i2cset` and `i2cget` can be used to write/read data to/from I2C devices.
### SPI
You can use `spi-pipe` to test SPI comms.

## Troubleshooting
If for some reason one or more of the commands fail, check if variables you modified are sane first.

Some raspi-config commands might don't work as expected when ran in qemu, such as enabling I2C or SPI.\
If that's the case, you can use EXTRACMDS to apply your changes manually.

Then, depending on where the execution failed, you might encounter a few issues when trying to run the script again:
* Qemu might still be running: Kill qemu-system-aarch64 manually
* One of the partitions might still be mounted: Check if any of the partitions are still mounted on root/ and boot/, if so, unmount them