import time
import threading
from jetmulticam import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline(["/dev/video0", "/dev/video1"])

    print(p.running())

    while (True):
        p.read(0)
        time.sleep(0.1)
