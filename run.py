import time

from jetmulticam import MultiCamPipeline
from jetmulticam.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    # pipeline = MultiCamPipeline(n_cams=3, models=[PeopleNet.DLA1, DashCamNet.DLA0])
    pipeline = MultiCamPipeline(n_cams=3, models=[PeopleNet.DLA1])
    pipeline.start()
    pipeline.wait_ready()

    while pipeline.running():
        print(pipeline.images[0].shape) # np.ndarray 
        print(pipeline.detections[0])
        time.sleep(1)
