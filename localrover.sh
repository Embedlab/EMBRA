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

if [[ "x${RUN_SERIAL}" == "x1" ]]; then
  info "Installing Minicom"
  ( set -x
    sudo apt-get install -y minicom
  ) || die "Installing Minicom failed"
fi

if [[ "x${RUN_RASPICONF}" == "x1" ]]; then
  info "Running raspi-config commands"
  ( set -x
  for cmd in "${RASPICMDS[@]}"; do
    sudo raspi-config nonint $cmd
  done
  ) || die "raspi-config failed"
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
