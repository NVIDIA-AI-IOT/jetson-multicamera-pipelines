import time

from jetvision import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline([0, 1])

    print(p.running())

    for _ in range(100):
        arr = p.read(0)
        if arr is not None:
            print(arr.shape)
        time.sleep(0.1)
