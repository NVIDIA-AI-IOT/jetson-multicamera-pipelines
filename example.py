import time

from jetvision import CameraPipelineDNN
from jetvision.models import PeopleNet, DashCamNet

import logging

log = logging.getLogger("jetvision")
log.setLevel(logging.WARN)

if __name__ == "__main__":

    pipeline = CameraPipelineDNN(
        cameras=[5, 8, 2],
        models=[
            # PeopleNet.DLA1,
            PeopleNet.DLA1,
            DashCamNet.DLA0
        ],
        save_video=True,
        save_video_folder="/home/nx/logs/videos",
        display=True,
    )

    while pipeline.running():
        print(pipeline.images[0].shape)  # np.ndarray
        print(pipeline.detections[0])
        time.sleep(1 / 30)
