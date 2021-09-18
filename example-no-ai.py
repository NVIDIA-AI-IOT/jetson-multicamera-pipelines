import time

from jetvision import CameraPipeline

if __name__ == "__main__":

    p = CameraPipeline(2)

    while True:
        a = p.read()
        print(a.shape)
        time.sleep(0.1)
