install_logitech_drivers()
{
    wget https://github.com/jetsonhacks/logitech-f710-module/raw/master/bin/l4t-32-5-1/hid-logitech.ko -O hid-logitech.ko
    wget https://raw.githubusercontent.com/jetsonhacks/logitech-f710-module/master/install-module.sh -O install-module.sh
    sudo install-module.sh
}

usb_permissions()
{
    # Let user talk to maestro servo controller
    sudo adduser $USER dialout;
}

echo "Installing..."
pip3 install -r requirements.txt
install_logitech_drivers
usb_permissions
