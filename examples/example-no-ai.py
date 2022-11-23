import time

from jetmulticam import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline(["/dev/video0", "/dev/video1"])

    print(p.running())

    for _ in range(100):
        arr = p.read(0)
        if arr is not None:
            print(arr.shape)
        time.sleep(0.1)
