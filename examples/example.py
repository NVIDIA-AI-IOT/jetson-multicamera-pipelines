import time
from jetvision import CameraPipelineDNN
from jetvision.models import PeopleNet, DashCamNet

if __name__ == "__main__":

    pipeline = CameraPipelineDNN(
        cameras=[2, 5, 8],
        models=[
            PeopleNet.DLA1,
            DashCamNet.DLA0,
            # PeopleNet.GPU
        ],
        save_video=True,
        save_video_folder="/home/nx/logs/videos",
        display=True,
    )

    while pipeline.running():

        # We can access the captured images here.
        # For example `pipeline.images` is a list of numpy arrays for each camera
        # In my case (RGB 1080p image), `arr` will be np.ndarray with shape: (1080, 1920, 3)
        arr = pipeline.images[0]
        print(type(arr))

        # Detections in each image are available here as a list of dicts:
        dets = pipeline.detections[0]
        print(dets)

        # Assuming there's one detection in `image[0]`, `dets` can look like so:
        # [{
        #     'class': 'person',
        #     'position': (361.31, 195.60, 891.96, 186.05), # bbox (left, width, top, height)
        #     'confidence': 0.92
        # }]

        # Main thread is not tied in any computation.
        # We can perform any operations on our images.
        avg = pipeline.images[0].mean()
        print(avg)
        time.sleep(1 / 30)
