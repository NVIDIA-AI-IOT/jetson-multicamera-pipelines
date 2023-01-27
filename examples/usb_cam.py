# import time
from jetmulticam import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline(["/dev/video0", "/dev/video1"])
    print("Running on Single threaded mode")
    while (True):
        p.read_singleThreaded()
