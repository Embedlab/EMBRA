#! /bin/bash

show_help() {
  echo "Usage: set_relay [CHANNEL] [STATE]"
  echo
  echo "Controls relays on the specified channel."
  echo
  echo "CHANNEL:"
  echo "  CH1    Relay channel 1"
  echo "  CH2    Relay channel 2"
  echo "  CH3    Relay channel 3"
  echo
  echo "STATE:"
  echo "  ON     Turns the relay on (connects NO contact)"
  echo "  OFF    Turns the relay off (connects NC contact)"
  echo
  echo "Relay contacts:"
  echo "  NO (Normally Open) - Contact is open when the relay is off, closes when the relay is on."
  echo "  NC (Normally Closed) - Contact is closed when the relay is off, opens when the relay is on."
  echo
  echo "Examples:"
  echo "  set_relay CH1 ON    # Turns relay channel 1 on (connects NO)"
  echo "  set_relay CH2 OFF   # Turns relay channel 2 off (connects NC)"
}

for arg in "$@"; do
  case $arg in
    -h|--help)
      show_help
      exit 0
      ;;
  esac
done

if [ $1 == 'CH1' ]
then
 ch=538
elif [ $1 == 'CH2' ]
then
 ch=532
elif [ $1 == 'CH3' ]
then
 ch=533
else
 echo "Parameter error"
 exit
fi

if [ $2 == 'ON' ]
then
 state=0
elif [ $2 == 'OFF' ]
then
 state=1
else
 echo "Parameter error"
 exit
fi

echo $ch > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio$ch/direction
echo $state > /sys/class/gpio/gpio$ch/value
echo Relay $1 $2
