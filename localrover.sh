#!/bin/bash

source ./env

function info() {
  echo -ne "\e[92m"
  echo "$*"
  echo -ne "\e[0m"
}

function die() {
  echo -ne "\e[31m"
  echo "$*"
  echo -ne "\e[0m"
  exit 1
}

APPNAME=remote-rover

info "Connecting to the internet."
ping -c 1 8.8.8.8 &> /dev/null

if [[ $? -eq 0 ]]; then
  info "Connected to the internet."
else
  die "Internet cconnection failed"
fi

if [[ "x${RUN_UPDATE}" == "x1" ]]; then
  info "Updating APT"
  ( set -x
    sudo apt-get update
  ) || die "Updating APT failed"
fi

if [[ "x${RUN_UPGRADE}" == "x1" ]]; then
  info "Updating system"
  ( set -x
  sudo apt-get upgrade -y
  ) || die "Updating system failed"
fi

if [[ "x${RUN_PKGS}" == "x1" ]]; then
  info "Installing extra packages ($(echo $PKGS | xargs | sed 's/ /, /g'))"
  ( set -x
  sudo apt-get install -y $PKGS
  ) || die "Installing extra packages failed"
fi

if [[ "$RUN_ETH" == "1" ]]; then
  info "Setting up static Ethernet"
  sudo ifconfig eth0 down
  sudo ifconfig eth0 up
fi

if [[ "$RUN_WLAN" == "1" ]]; then
  info "Setting up static Wlan"
  sudo raspi-config nonint do_wifi_country PL # we can add variable for that
  sudo rfkill unblock wifi
  sudo ifconfig wlan0 up
fi

if [[ "x${RUN_SERIAL}" == "x1" ]]; then
  info "Installing Minicom"
  ( set -x
    sudo apt-get install -y minicom
  ) || die "Installing Minicom failed"
fi

if [[ "x${RUN_STM32}" == "x1" ]]; then
  info "Enabling STM32"
  ( set -x
    sudo apt install -y at git ser2net stlink-tools || { echo "Installing dependencies failed"; exit 1; }
    git clone https://github.com/eosti/remote-stm32.git || { echo "Git clone failed"; exit 1; }
    cd remote-stm32 || { echo "Failed to enter directory"; exit 1; }
    sudo ./install.sh || { echo "Installation failed"; exit 1; }
    cd ..
    rm -rf remote-stm32
  ) || die "Enabling STM32 failed"
fi

if [[ "x${RUN_RELAY}" == "x1" ]]; then
  info "Enabling Waveshare RPi Relay Board"
  ( set -x
    sudo apt install -y git
    git clone https://github.com/WiringPi/WiringPi
    cd WiringPi
    ./build  
    cd ..
    rm -rf WiringPi
  ) || die "Enabling Waveshare RPi Relay Board failed"
fi

if [[ "x${RUN_CAMERA}" == "x1" ]]; then
  info "Enabling remote camera"
  ( set -x
    sudo apt install -y git
    git clone https://github.com/ayufan-research/camera-streamer.git --recursive
    sudo apt install -y libavformat-dev libavutil-dev libavcodec-dev libcamera-dev liblivemedia-dev v4l-utils pkg-config xxd build-essential cmake libssl-dev
    cd camera-streamer/
    make
    sudo make install 
    sudo systemctl enable /etc/systemd/system/camera-streamer.service
    sudo systemctl start camera-streamer.service
    cd ..
    rm -rf camera-streamer
  ) || die "Enabling remote camera"
fi

if [[ "x${RUN_CURRENT_MONITOR}" == "x1" ]]; then
  info "Enabling Power Monitor HAT"
  ( set -x
    sudo apt install -y python3-pip
    sudo pip3 install --break-system-packages adafruit-circuitpython-ina219
  ) || die "Enabling Power Monitor HAT failed"
fi

if [[ "x${RUN_CAN}" == "x1" ]]; then
  info "Enabling CAN bus"
  ( set -x
    sudo apt install -y can-utils
    sudo ip link set can0 up type can bitrate $CAN_BITRATE   dbitrate $CAN_DBITRATE restart-ms 1000 berr-reporting on fd on
    sudo ip link set can1 up type can bitrate $CAN_BITRATE   dbitrate $CAN_DBITRATE restart-ms 1000 berr-reporting on fd on
    sudo ifconfig can0 txqueuelen 65536
    sudo ifconfig can1 txqueuelen 65536
  ) || die "Enabling CAN bus failed"
fi

if [[ "x${RUN_RASPICONF}" == "x1" ]]; then
  info "Running raspi-config commands"
  ( set -x
  for cmd in "${RASPICMDS[@]}"; do
    sudo raspi-config nonint $cmd
  done
  ) || die "raspi-config failed"
fi

if [[ "x${RUN_LOGGING}" == "x1" ]]; then
  info "Running extra commands"
  ( set -x
    sudo apt install -y python3-opencv python3-picamera2
    sudo pip3 install -r requirements.txt --break-system-packages
  ) || die "Extra commands failed"
fi

if [[ "x${RUN_EXTRA}" == "x1" ]]; then
  info "Running extra commands"
  ( set -x
  for cmd in "${EXTRACMDS[@]}"; do
    $cmd
  done
  ) || die "Extra commands failed"
fi

if [[ "x${RUN_NETWORK}" == "x1" ]] && [[ "x${NETDNS}" != "x" ]]; then
  info "Setting up target DNS settings"
  ( set -x
  echo nameserver $NETDNS | sudo tee /etc/resolv.conf
  ) || die "Setting up DNS failed"
fi

sudo rm -f /home/$USERNAME/localrover.sh /home/$USERNAME/env /etc/systemd/system/localrover.service
sudo sed -i '/sudo systemctl daemon-reload && systemctl enable localrover.service/d' /etc/rc.local
sudo sed -i '/sudo systemctl start localrover.service/d' /etc/rc.local

if [[ "$RUN_WLAN" == "1" ]]; then
  sudo reboot now
fi
