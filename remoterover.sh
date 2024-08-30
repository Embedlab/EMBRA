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

KERNELFILE=kernel8.img
DTBFILE=bcm2710-rpi-3-b-plus.dtb

function wait_for_ssh() {
  while ! (sleep 1) | telnet localhost 2222 2>/dev/null | grep -q SSH ; do sleep 1 ; echo -n . ; done
  echo -e "\nSSH is up"
}

function sshpi(){
  sshpass -e ssh -o StrictHostKeychecking=no -o UserKnownHostsFile=/dev/null pi@localhost -p2222 $*
}

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

if [[ "x${RUN_UPDATE}" == "x1" ]] || [[ "x${RUN_UPGRADE}" == "x1" ]] || [[ "x${RUN_PKGS}" == "x1" ]] || [[ "x${RUN_RASPICONF}" == "x1" ]] || [[ "x${RUN_EXTRA}" == "x1" ]]; then
  QEMU_NEEDED=1
fi

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

if [[ "x${QEMU_NEEDED}" == "x1" ]] && [[ "x${BOOT_NEEDED}" == "x1" ]]; then
  info "Getting kernel and dtb"
  ( set -x
  cp boot/$KERNELFILE .
  cp boot/$DTBFILE .
  ) || die "Copying kernel/dtb failed"
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
  ) || "Unmounting boot failed"
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

if [[ "x${RUN_I2C}" == "x1" ]]; then
  info "Adding i2c-dev to default modules"
  ( set -x
  echo "i2c-dev" | sudo tee -a root/etc/modules
  ) || die "Adding i2c-dev to default modules failed"
fi


if [[ "x${RUN_SSHKEYS}" == "x1" ]]; then
  info "Adding a provided SSH key(s) to authorized_keys"
  ( set -x
  mkdir -p root/home/$USERNAME/.ssh
  echo "$SSHKEYS" > root/home/$USERNAME/.ssh/authorized_keys
  chmod 644 root/home/$USERNAME/.ssh/authorized_keys
  ) || die "Addding SSH keys failed"
fi

if [[ "x${RUN_NETWORK}" == "x1" ]]; then
  info "Setting up network config"

  if [[ "$RUN_ETH" == "1" ]]; then
    IFCFG="root/etc/network/interfaces.d/${APPNAME}.conf"
    ( set -x
    [[ "x${NETIP}" != x ]] && echo "# Automatically added by $APPNAME
auto $NETIF
iface $NETIF inet static
    address $NETIP" | sudo tee -a $IFCFG
    [[ "x${NETMASK}" != x ]]  && echo "    netmask $NETMASK" | sudo tee -a $IFCFG
    [[ "x${NETGW}" != x ]]    && echo "    gateway $NETGW" | sudo tee -a $IFCFG
    [[ "x${NETDNS}" != x ]]    && echo "    dns-nameservers $NETDNS" | sudo tee -a $IFCFG
    [[ "x${NETMETRIC}" != x ]]    && echo "    metric $NETMETRIC" | sudo tee -a $IFCFG
    [[ "x${NETEXTRA}" != x ]] && echo "$NETEXTRA" | sudo tee -a $IFCFG
    )
  fi

  if [[ "$RUN_WLAN" == "1" ]]; then
    IFCFG="root/etc/network/interfaces.d/${APPNAME}.conf"
    ( set -x
    echo "# Automatically added by $APPNAME
auto $WLAN_NETIF" | sudo tee -a $IFCFG

    if [[ "$RUN_WLAN_DHCP" == "1" ]]; then
        echo "iface $WLAN_NETIF inet dhcp" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETMETRIC}" != x ]] && echo "    metric $WLAN_NETMETRIC" | sudo tee -a $IFCFG
        [[ "x${SSID}" != x ]]          && echo "    wpa-ssid $SSID" | sudo tee -a $IFCFG
        [[ "x${PSK}" != x ]]           && echo "    wpa-psk $PSK" | sudo tee -a $IFCFG
        [[ "x${WLAN_NETEXTRA}" != x ]] && echo "$WLAN_NETEXTRA" | sudo tee -a $IFCFG
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

if [[ "x${QEMU_NEEDED}" == "x1" ]]; then
  info "Running QEMU in background..."
  ( set -x
  qemu-system-aarch64 -machine raspi3b -cpu cortex-a72 -dtb $DTBFILE \
  -m 1G -smp 4 -kernel $KERNELFILE -drive file=${IMG},format=raw -daemonize -display none \
  -append "rw dwc_otg.lpm_enable=0 root=/dev/mmcblk0p2 rootdelay=1" \
  -device usb-net,netdev=net0 -netdev user,id=net0,hostfwd=tcp::2222-:22
  ) || die "Runnning QEMU failed"

  info "Waiting for SSH"
  wait_for_ssh
fi

if [[ "x${RUN_UPDATE}" == "x1" ]]; then
  info "Updating APT"
  ( set -x
  sshpi sudo apt-get update
  ) || die "Updating APT failed"
fi

if [[ "x${RUN_UPGRADE}" == "x1" ]]; then
  info "Updating system"
  ( set -x
  sshpi sudo apt-get upgrade -y
  ) || die "Updating system failed"
fi

if [[ "x${RUN_PKGS}" == "x1" ]]; then
  info "Installing extra packages ($(echo $PKGS | xargs | sed 's/ /, /g'))"
  ( set -x
  sshpi sudo apt-get install -y $PKGS
  ) || die "Installing extra packages failed"
fi

if [[ "x${RUN_RASPICONF}" == "x1" ]]; then
  info "Running raspi-config commands"
  ( set -x
  for cmd in "${RASPICMDS[@]}"; do
    sshpi sudo raspi-config nonint $cmd
  done
  ) || die "raspi-config failed"
fi

if [[ "x${RUN_EXTRA}" == "x1" ]]; then
  info "Running extra commands"
  ( set -x
  for cmd in "${EXTRACMDS[@]}"; do
    sshpi $cmd
  done
  ) || die "Extra commands failed"
fi

if [[ "x${RUN_NETWORK}" == "x1" ]] && [[ "x${NETDNS}" != "x" ]]; then
  info "Setting up target DNS settings"
  ( set -x
  sshpi "echo nameserver $NETDNS | sudo tee /etc/resolv.conf"
  )
fi


if [[ "x${QEMU_NEEDED}" == "x1" ]]; then
  info "Shutting down QEMU"
  ( set -x
  sshpi "sudo shutdown -h now"
  )
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
  rm -f $KERNELFILE $DTBFILE
  rmdir boot root
  )
fi
