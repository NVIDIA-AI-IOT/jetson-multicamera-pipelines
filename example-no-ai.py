import time

from jetvision import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline([2,5,8])

    while True:
        arr = p.read(0)
        if arr is not None:
            print(arr.shape)
        time.sleep(0.1)
