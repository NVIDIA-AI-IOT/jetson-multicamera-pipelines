# Robot
Code related to driving / controlling the robot.
Exposes "drive-by-wire" robot API that can be controlled via `set_throttle()` and `set_steering()`.

All what's needed to create a manually operated robot, or a building block for an autonomous robot.

## What's inside 
```shell
├── controler
│   ├── hid-logitech.ko # Kernel driver for logitech game controller
│   └── gamepad.py # Code for receiving logitech wireless controller inputs
├── drive-with-gamepad.py
└── vehicle
    ├── maestro.py # Pololu maestro driver
    └── vehicle.py # Code for controlling the robot (throttle+steering)
```


## Installation

```shell
bash install.sh 
pip3 install -r requirements.txt
```

Logitech kernel drivers are for `JP4.5.1`. For different Jetpack versions refer to JetsonHacks' [repository](https://github.com/jetsonhacks/logitech-f710-module/).

## Usage
```shell
python3 drive-by-wire.py
```
