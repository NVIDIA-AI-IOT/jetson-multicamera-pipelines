

import maestro
import time

servo = maestro.Controller('/dev/ttyACM0')

class THR:
    # Throttle params
    CH = 0 # channel
    STOP = 5602 # us (pulse width at which the motor is stopped)
    DEADBAND_F = 5725 # (motors start turning slightly forward)
    DEADBAND_B = 5480 # (motors start turning slightly backward)

    FW = 5825 # go slowly forward
    BW = 5380 # go slowly backward
    
    FW_MAX = 8000
    BW_MAX = 4000

class STEER:
    CH = 1
    C = 6000 # center
    R = 8000 # left 
    L = 4000 # right


servo.setTarget(STEER.CH, STEER.C)

for i in range(THR.STOP, THR.FW, 1):
    print(f"Speed {i}", end='\r')
    time.sleep(0.01)
    servo.setTarget(THR.CH, i)
print("")

print("Stop")
servo.setTarget(THR.CH, THR.STOP)
time.sleep(1)

print("Turn Right")
servo.setTarget(STEER.CH, STEER.R)
time.sleep(1)

print("Center")
servo.setTarget(STEER.CH, STEER.C)
time.sleep(1)

print("Turn Left")
servo.setTarget(STEER.CH, STEER.L)
time.sleep(1)

print("Center")
servo.setTarget(STEER.CH, STEER.C)
time.sleep(1)


servo.close()


