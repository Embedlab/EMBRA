#!/bin/bash

# Dependencies:
# * qemu-system-aarch64
# * fdisk,  xz-tools
# * sudo with either an interactive shell or root access for temporarily mounting the image
# * sshpass

# Get options from env file
source ./env
# These can be temporarily overwritten here if needed

##################################
# No user-serviceable parts below

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

IMG=${IMGXZ%.xz}

if [[ "x${RUN_USERSETUP}" == "x1" ]] || [[ "x${RUN_ENABLESSH}" == "x1" ]] || [[ "x${RUN_I2C}" == "x1" ]] || [[ "x${RUN_SPI}" == "x1" ]]; then
  BOOT_NEEDED=1
fi

if [[ "x${QEMU_NEEDED}" == "x1" ]] && [ ! -e $KERNELFILE -o ! -e $DTBFILE ]; then
  BOOT_NEEDED=1
fi

if [[ "x${RUN_I2C}" == "x1" ]] || [[ "x${RUN_NETWORK}" == "x1" ]] || [[ "x${RUN_SSHKEYS}" == "x1" ]] || [[ "x${RUN_HOSTNAME}" == "x1" ]]; then
  ROOTFS_NEEDED=1
fi

if [[ "x${RUN_PREP}" == "x1" ]]; then
  if [[ x$FORCE == "x1" ]] || ! [ -f $IMG ]; then
    info "Unpacking raspi image"
    ( set -x
    unxz -k $IMGXZ
    )
  else
    echo "Already unpacked. If you want to redo the whole setup, remove the .img file or set FORCE=1"
  fi

  oldsize=$(stat --printf="%s" $IMG)
  if factor $oldsize | cut -d: -f2  | grep -qE "[^2 ]"; then
    info "Resizing image to a power of 2 size, needed by qemu"
    newsize=$(echo "x=l($oldsize)/l(2); scale=0; 2^((x+1)/1)" | bc -l)
    info "New size determined to be $(($newsize/(1024**3)))GiB"
    ( set -x
    qemu-img resize -f raw $IMG $newsize
    ) || die "Image resize failed"
  fi
fi

parts="$(fdisk -l $IMG)"
OFFB=$(($(echo "$parts" | grep img1 | xargs echo | cut -d' ' -f2)*512))
OFFR=$(($(echo "$parts" | grep img2 | xargs echo | cut -d' ' -f2)*512))

if [[ "x${BOOT_NEEDED}" == "x1" ]]; then
  info "Mounting boot partition to ./img, sudo password will be needed."
  ( set -x
  mkdir -p boot
  sudo mount -o loop,offset=$OFFB $IMG boot
  )
  ! mountpoint boot && die "Mounting boot failed"
fi

if [[ "x${RUN_USERSETUP}" == "x1" ]]; then
  info "Setting user password"
  ( set -x
  shadowstr=$(openssl passwd -6 "$USERPASS")
  echo "${USERNAME}:${shadowstr}" | sudo tee boot/userconf
  ) || die "Setting user password failed"
fi

if [[ "x${RUN_I2C}" == "x1" ]]; then
  info "Enabling I2C"
  ( set -x
  echo "dtparam=i2c_arm=on # Added by $APPNAME" | sudo tee -a boot/config.txt
  ) || die "Enabling I2C failed"
fi

if [[ "x${RUN_SPI}" == "x1" ]]; then
  info "Enabling SPI"
  ( set -x
  echo "dtparam=spi=on # Added by $APPNAME" | sudo tee -a boot/config.txt
  ) || die "Enabling SPI failed"
fi

if [[ "x${RUN_SERIAL}" == "x1" ]]; then
  info "Enabling UART"
  ( set -x
  echo "enable_uart=1 # Added by $APPNAME" | sudo tee -a boot/config.txt
  sudo sed -i 's/console=serial0,115200 //;s/console=ttyS0,115200 //' boot/cmdline.txt
  ) || die "Enabling UART failed"
fi

if [[ "x${RUN_ENABLESSH}" == "x1" ]]; then
  info "Enabling SSH"
  ( set -x
  sudo touch boot/ssh
  ) || die "Enabling SSH failed"
fi

if [[ "x${BOOT_NEEDED}" == "x1" ]]; then
  info "Unmounting boot"
  ( set -x
  sudo umount boot
  ) || die "Unmounting boot failed"
  sync
fi

if [[ "x${ROOTFS_NEEDED}" == "x1" ]]; then
  info "Mounting rootfs partition to ./root, sudo password will be needed."
  ( set -x
  mkdir -p root
  sudo mount -o loop,offset=$OFFR $IMG root
  )
  ! mountpoint root && die "Mounting root failed!"
fi

if [[ "x${ROOTFS_NEEDED}" == "x1" ]]; then

  IMAGE_MOUNT_POINT="root"
  SCRIPT_PATH="/home/$USERNAME/localrover.sh"
  ENV_PATH="$IMAGE_MOUNT_POINT/home/$USERNAME/env"
  SERVICE_PATH="$IMAGE_MOUNT_POINT/etc/systemd/system/localrover.service"

  info "Copying local script to rootfs"
  (
    set -x
    cp localrover.sh "$IMAGE_MOUNT_POINT"/"$SCRIPT_PATH"
    cp env "$ENV_PATH"
    echo "Creating systemd service"

    cat <<EOF | sudo tee "$SERVICE_PATH"
[Unit]
Description=Local Rover Script
After=network.target

[Service]
ExecStart=$SCRIPT_PATH
WorkingDirectory=/home/$USERNAME
User=$USERNAME
Group=$USERNAME
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    sed -i '${/exit 0/d;}' root/etc/rc.local
    echo "sudo systemctl daemon-reload && systemctl enable localrover.service" >> root/etc/rc.local
    echo "sudo systemctl start localrover.service" >> root/etc/rc.local
    echo "exit 0" >> root/etc/rc.local

    info "Systemd service created and started."
  ) || die "Copying local script and creating service failed"
fi

if [[ "x${RUN_I2C}" == "x1" ]]; then
  info "Adding i2c-dev to default modules"
  ( set -x
  echo "i2c-dev" | sudo tee -a root/etc/modules
  ) || die "Adding i2c-dev to default modules failed"
fi

if [[ "x${RUN_NETWORK}" == "x1" ]]; then
  info "Setting up network config"

  if [[ "$RUN_ETH" == "1" ]]; then
    IFCFG="root/etc/network/interfaces.d/${APPNAME}.conf"
    (
      set -x
      [[ "x${NETIP}" != x ]] && echo "# Automatically added by $APPNAME
auto $NETIF
iface $NETIF inet static
    address $NETIP" | sudo tee -a $IFCFG
      [[ "x${NETMASK}" != x ]]  && echo "    netmask $NETMASK" | sudo tee -a $IFCFG
      [[ "x${NETGW}" != x ]]    && echo "    gateway $NETGW" | sudo tee -a $IFCFG
      [[ "x${NETDNS}" != x ]]   && echo "    dns-nameservers $NETDNS" | sudo tee -a $IFCFG
      [[ "x${NETMETRIC}" != x ]] && echo "    metric $NETMETRIC" | sudo tee -a $IFCFG
      [[ "x${NETEXTRA}" != x ]] && echo "$NETEXTRA" | sudo tee -a $IFCFG
    )
  fi

  if [[ "$RUN_WLAN" == "1" ]]; then
    IFCFG="root/etc/network/interfaces.d/${APPNAME}.conf"
    (
      set -x
      echo "# Automatically added by $APPNAME
auto $WLAN_NETIF" | sudo tee -a $IFCFG

      if [[ "$RUN_WLAN_DHCP" == "1" ]]; then
        echo "iface $WLAN_NETIF inet dhcp" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETMETRIC}" != x ]] && echo "    metric $WLAN_NETMETRIC" | sudo tee -a $IFCFG
        [[ "x${SSID}" != x ]]           && echo "    wpa-ssid $SSID" | sudo tee -a $IFCFG
        [[ "x${PSK}" != x ]]            && echo "    wpa-psk $PSK" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETEXTRA}" != x ]]  && echo "$WLAN_NETEXTRA" | sudo tee -a $IFCFG
      else
        echo "iface $WLAN_NETIF inet static
    address $WLAN_NETIP" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETMASK}" != x ]]  && echo "    netmask $WLAN_NETMASK" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETGW}" != x ]]    && echo "    gateway $WLAN_NETGW" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETDNS}" != x ]]   && echo "    dns-nameservers $WLAN_NETDNS" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETMETRIC}" != x ]] && echo "    metric $WLAN_NETMETRIC" | sudo tee -a $IFCFG
        [[ "x${SSID}" != x ]]          && echo "    wpa-ssid $SSID" | sudo tee -a $IFCFG
        [[ "x${PSK}" != x ]]           && echo "    wpa-psk $PSK" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETEXTRA}" != x ]] && echo "$WLAN_NETEXTRA" | sudo tee -a $IFCFG
      fi
    )
  fi
fi

if [[ "x${RUN_HOSTNAME}" == "x1" ]]; then
  info "Changing hostname to $RASPIHOST"
  ( set -x
  sudo sed -i "s/raspberrypi/${RASPIHOST}/g" root/etc/hostname
  sudo sed -i "s/raspberrypi/${RASPIHOST}/g" root/etc/hosts
  ) || die "Changing hostname failed"
fi

if [[ "x${ROOTFS_NEEDED}" == "x1" ]]; then
  info "Unmounting root"
  ( set -x
  sudo umount root
  ) || die "Unmounting root failed"
  sync
fi

if [[ "x${RUN_SHRINK}" == "x1" ]]; then
  info "Shrinking image back"
  actualsize=$(($(fdisk -l $IMG | grep img2 | xargs echo | cut -d' ' -f3)*512))
  ( set -x
  qemu-img resize -f raw --shrink $IMG $actualsize
  )
fi

if [[ "x${RUN_CLEANUP}" == "x1" ]]; then
  info "Cleaning up temp files"
  ( set -x
  rmdir boot root
  )
fi
