from panoptes import MultiCamPipeline
import vehicle
import depth
import SLAM

pipeline = MultiCamPipeline(
    n_cams=3,  # dynamically create pipeline for n cameras 1..6
    # choose the components we need a la carte / one-by-one
    detect_objects=True,
    detect_faces=True,
    save_images=True,  # much better than cv2.imsave
    save_h264=True,
    copy=True,  # returns views (more memory efficient, but readonly) or copies (convenient, ok to r/w).
)

pipeline.cameras[0].image  # (1080, 1920, 3) np array already mapped to host
pipeline.cameras[0].obj_dets
pipeline.cameras[0].face_dets


while True:
    dets = pipeline.cameras[0].obj_dets
    if any(dets == "class_person"):
        robot.stop()


# Depth part:
# depth = Depth(algo='SBM', backend='PVA')
# depth = Depth(algo='SBM', backend='OpenCV')
dpth = Depth(algo="SBM", backend="CUDA")

robot.forward(timeout=2)

if any(dpth.depth_map) < 0.5:
    robot.stop()
