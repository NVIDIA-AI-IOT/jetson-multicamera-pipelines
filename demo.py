

from multicam_robot import robot, Rgb, Depth, SLAM

rgb = Rgb(obj_detections=True, save_images=True, save_h264=True, copy=True)

dpth = Depth(algo='SBM', backend='CUDA')
# depth = Depth(algo='SBM', backend='PVA')
# depth = Depth(algo='SBM', backend='OpenCV')

robot.forward(timeout=2)

if any(dpth.depth_map)) < 0.5:
    robot.stop()



##############################################################################


from multicam_robot import robot, Rgb, Depth, SLAM

rgb = Rgb(obj_detections=True, save_images=True, save_h264=True, copy=True)

dpth = Depth(algo='SBM', backend='CUDA')
# depth = Depth(algo='SBM', backend='PVA')
# depth = Depth(algo='SBM', backend='OpenCV')

robot.forward(timeout=2)

if any(dpth.depth_map)) < 0.5:
    robot.stop()



