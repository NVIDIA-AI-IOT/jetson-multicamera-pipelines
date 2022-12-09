import time
from jetmulticam import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline(["/dev/video0", "/dev/video1"])

    while (True):
        p.read(0)
        # time.sleep(0.1)
