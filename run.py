import time

from jetvision import MultiCamPipeline
from jetvision.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    pipeline = MultiCamPipeline(
        sensor_id_list=[2, 0, 1],
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
