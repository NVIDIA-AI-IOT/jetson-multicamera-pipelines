import time

from jetvision import CameraPipeline
from jetvision.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    p = CameraPipeline(0)
    p.wait_ready()

    while True:
        a = p.read()
        print(a.shape)
        # time.sleep(0.1)
