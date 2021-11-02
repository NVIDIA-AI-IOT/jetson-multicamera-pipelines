from threading import Thread
import time
import collections
from concurrent.futures import ThreadPoolExecutor

from jetmulticam import CameraPipelineDNN
from jetmulticam.models import PeopleNet, DashCamNet

# robot related packages
from controller import ManualController
from vehicle import Vehicle


def find_closest_human(dets_l, dets_c, dets_r):

    htf = None
    htf_area = -1
    htf_im = None

    for dets, im in zip((dets_l, dets_c, dets_r), ["l", "c", "r"]):
        humans = [det for det in dets if det["class"] == "person"]
        for human in humans:
            (l, w, t, h) = human["position"]
            if w * h > htf_area:
                htf = human  # htf -> human to follow
                htf_area = w * h
                htf_im = im

    return (htf, htf_im)


def dets2steer(dets):
    W = 1920  # Image width
    human, which_im = find_closest_human(*dets)
    steer = 0
    if which_im == "c":
        (l, w, _, _) = human["position"]
        center = l + w / 2
        steer = (center - W / 2) / W * 2
    elif which_im == "l":
        steer = -1
    elif which_im == "r":
        steer = 1
    return steer


class Filter:
    def __init__(self, window=10):
        self._q = collections.deque(maxlen=window)

    def __call__(self, sample):
        self._q.append(sample)
        value = np.array(self._q).mean()
        return value


def main_follow_person():
    controller = ManualController()
    vehicle = Vehicle()
    filter = Filter(20)

    pipeline = CameraPipelineDNN(
        cameras=[5, 2, 8],
        models=[
            PeopleNet.DLA1,
            DashCamNet.DLA0,
        ],
        save_video=True,
        save_video_folder="/home/nx/video-output",
        display=True,  # just for visual debug
    )

    try:
        while pipeline.running():

            if controller.right_pressed():
                # If button pressed, follow person
                velocity = 0.3
                steering = dets2steer(pipeline.detections)
                steering = filter(steering)
                print(steering)
                vehicle.set_throttle(velocity)
                vehicle.set_steering(steering)
            else:
                # Fall back to manual steering
                velocity = controller.throttle()
                steering = controller.steering()
                vehicle.set_throttle(velocity)
                vehicle.set_steering(steering)

            # # Debug messages
            dbg_str = ""
            dbg_str += f"Center: {pipeline.fps()[0]:0.2f} FPS Front: {pipeline.fps()[1]:0.2f} FPS Right: {pipeline.fps()[2]:0.2f}FPS | "
            dbg_str += (
                f"Throttle: {round(velocity, 2)} Steering: {round(controller.s, 2)} | "
            )
            dbg_str += f"Train: {controller.train_mode()} Auto: {controller.autonomous_mode()} N. dets: {len(pipeline.detections[0])} | "
            # dbg_str += f"Dets: {pipeline.detections}"
            print(dbg_str)

            time.sleep(1 / 30)  # Cap the main thread at 30 FPS

    except Exception as e:
        print(e)
    finally:
        pipeline.stop()
        controller.stop()
        vehicle.stop()


def main_manual():
    controller = ManualController()
    vehicle = Vehicle()

    pipeline = CameraPipelineDNN(
        cameras=[5, 2, 8],
        models=[
            # PeopleNet.DLA1,
            # DashCamNet.DLA0,
            DashCamNet.GPU
        ],
        save_video=True,
        save_video_folder="/home/nx/jetvision-output",
        display=True,  # just for visual debug
    )

    try:
        while pipeline.running():

            velocity, human_steering = controller.t, controller.s

            vehicle.set_throttle(velocity)
            vehicle.set_steering(human_steering)

            # # Debug messages
            dbg_str = ""
            dbg_str += f"Center: {pipeline.fps()[0]:0.2f} FPS Front: {pipeline.fps()[1]:0.2f} FPS Right: {pipeline.fps()[2]:0.2f}FPS | "
            dbg_str += f"Throttle: {round(controller.t, 2)} Steering: {round(controller.s, 2)} | "
            dbg_str += f"Train: {controller.train_mode()} Auto: {controller.autonomous_mode()} N. dets: {len(pipeline.detections[0])} | "
            print(dbg_str)

            time.sleep(1 / 30)  # Cap the main thread at 30 FPS

    except Exception as e:
        print(e)
    finally:
        pipeline.stop()
        controller.stop()
        vehicle.stop()


if __name__ == "__main__":
    main_follow_person()
