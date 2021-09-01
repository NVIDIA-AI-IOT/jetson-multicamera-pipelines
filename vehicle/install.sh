# Install python packages
pip3 install -r requirements.txt
# let user talk to maestro over USB
sudo adduser $USER dialout
# Install logitech kernel driver
wget https://github.com/jetsonhacks/logitech-f710-module/raw/master/bin/l4t-32-5-1/hid-logitech.ko -O /tmp/hid-logitech.ko
wget https://raw.githubusercontent.com/jetsonhacks/logitech-f710-module/master/install-module.sh -O /tmp/install-module.sh
sudo /tmp/install-module.sh