import time
from JetCameras import IMX219, IMX185

if __name__ == "__main__":

    cam0 = IMX219(camera_id=0)
    cam1 = IMX219(camera_id=1)

    for i in range(0, 100):

        img = cam0.read()
        img2 = cam1.read()
        print(img[0, 0])
        time.sleep(0.01)

    cam0.close()
    cam1.close()
