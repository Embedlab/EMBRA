# RemoteRover
A versatile platform for remote access and support, tailored for Raspberry Pi hardware. It automates the configuration of RPi OS, network interfaces, and communication protocols (SPI/I2C/Ethernet), while supporting extensions for power management and real-time monitoring. With optional camera integration, it offers live video streaming, making it perfect for seamless remote operations.

## Prerequisites

Before using this project, ensure the following prerequisites are met:

1. **Linux or WSL (Windows Subsystem for Linux) OS available**

2. **Required Packages**
   Install the necessary packages by running the following commands:

   ```bash
   sudo apt update
   sudo apt install fdisk xz-utils sudo qemu-utils bc openssl coreutils grep sed systemd
   ```

3. **Raspberry Pi OS Image**
   Download the Raspberry Pi OS Lite image:
  - Go to the official Raspberry Pi website: [Raspberry Pi OS](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-32-bit)
  - Choose and download the **Raspberry Pi OS Lite** version (32-bit).

4. **Raspberry Pi board**  
   This script has been tested on the Raspberry Pi 4, but it should also work with other Raspberry Pi versions.

## Basic Usage

1. **Download the repository**  
   Clone or download the repository to your local machine.

2. **Prepare the RPi OS Image**  
   Copy the Raspberry Pi OS image into the repository folder and set the `IMGXZ` variable in the `env` file to the full image file name.

3. **Configure system details**  
   In the `env` file:
   - Set `RASPIHOST`, `USERNAME`, and `USERPASS` to define the host name, user, and password.

4. **Network settings**  
   In the `env` file:
   - **Ethernet (static IP):** Set `RUN_ETH=1`, `NETIP`, `NETMASK`, and `NETGW` for static IP configuration.
   - **WLAN:** Set `RUN_WLAN_DHCP=1` for DHCP or `RUN_WLAN=1` for a static IP. Specify `SSID` (Wi-Fi name), `PSK` (password), and static IP details (`WLAN_NETIP`, `WLAN_NETMASK`, `WLAN_NETGW`) if using static addresses.

5. **Enable features for the image**  
   Set the necessary `RUN_*` variables to 1 in the `env` file to enable specific features, for example: `RUN_I2C` for I2C communication support or `RUN_CAMERA`  to have a live view with Raspberry Pi Camera ( see details below). 

6. **Generate the image**  
   Run the following command to generate the custom Raspberry Pi OS image:

   ```bash
   sudo ./remoterover.sh
   ```

7. **Write the generated image to an SD Card**
   - Download and use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write the generated image to an SD card.
   - Select "Use custom" when choosing the image to write, and select the generated image.


## Feature Usage

### I2C communication feature
**Description:**  
This feature provides I2C communication with external devices as a master. The Raspberry Pi acts as the master and communicates with I2C slave devices.

**Hardware:**  
No specific hardware is required.
Connect to I2C slave devices using the following GPIO pins (as per [Raspberry Pi Pinout](https://pinout.xyz/pinout/i2c)): **GPIO 2 (SDA)** for Data and **GPIO 3 (SCL)** for Clock.

**Usage:**  
To scan/write and read from external I2C devices, use:  
```bash
  # Scan: 
  i2cdetect -y 1
  # Write:
  i2cset -y 1 <device_address> <register> <data>
  # Read: 
  i2cget -y 1 <device_address> <register>
```

### SPI communication feature
**Description:**  
This feature provides SPI communication with external devices as a master. The Raspberry Pi communicates with SPI slave devices.

**Hardware:**  
No specific hardware is required.
Connect to SPI slave devices using the SPI0 or SPI1 pins (as per [Raspberry Pi Pinout](https://pinout.xyz/pinout/spi)).

**Usage:**  
To exchange data on a specific SPI device using `spi-pipe`, use:  
```bash
  echo -n "data" | spi-pipe --spi /dev/spidev0.0
```

For more information on `spi-pipe`, use refer to [this page](https://manpages.debian.org/testing/spi-tools/spi-pipe.1.en.html)


## Troubleshooting
If for some reason one or more of the commands fail, check if variables you modified are sane first.

Some raspi-config commands might don't work as expected when ran in qemu, such as enabling I2C or SPI.\
If that's the case, you can use EXTRACMDS to apply your changes manually.

Then, depending on where the execution failed, you might encounter a few issues when trying to run the script again:
* Qemu might still be running: Kill qemu-system-aarch64 manually
* One of the partitions might still be mounted: Check if any of the partitions are still mounted on root/ and boot/, if so, unmount them