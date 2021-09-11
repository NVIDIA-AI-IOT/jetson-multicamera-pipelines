import time

from jetvision import CameraPipelineDNN
from jetvision.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    pipeline = CameraPipelineDNN(
        cameras=[2, 5, 8],
        models=[
            PeopleNet.DLA1,
            PeopleNet.DLA0
            ]
        )

    pipeline.start()
    pipeline.wait_ready()

    while pipeline.running():
        print(pipeline.images[0].shape)  # np.ndarray
        print(pipeline.detections[0])
        time.sleep(1)
