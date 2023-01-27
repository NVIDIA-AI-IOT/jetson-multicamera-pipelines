import time
import cv2
import threading
import os
import multiprocessing


class camThread():
    def __init__(self, previewName, camID, sharedMem):
        self.previewName = previewName
        self.camID = camID
        self.cam = cv2.VideoCapture(camID)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH,800)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT,600)
        self.cam.set(cv2.CAP_PROP_BUFFERSIZE,1)
        self.cam.set(cv2.CAP_PROP_FPS,30)
        self.condition = threading.Event()
        self.frame = 1
        self.sharedMem = sharedMem
        
    def getEvent(self):
        return self.condition

    def set(self):
        self.condition.set()
    
    def clear(self):
        self.condition.clear()

    def run(self):
        print("Starting " + self.previewName)
        while not self.cam.isOpened():
            continue
        self.thread = threading.Thread(target=self.singleThreadGetFrame,args=(),daemon=True)
        self.thread.start()
        self.singleThreadGetFrame()
        
    def singleThreadGetFrame(self):
        while True:
                rval, self.frame = self.cam.read()
                if (not self.sharedMem.empty()):
                    self.sharedMem.get()

                self.sharedMem.put(self.frame)

    def showFrame(self):
        try:
            cv2.imshow(self.previewName, self.frame)
            cv2.waitKey(1000)
        except Exception as e:
            pass

    def getFrame(self):
        return self.frame

    def camPreview(self, previewName):
        cv2.namedWindow(previewName)
        if self.cam.isOpened():  # try to get the first frame
            rval, frame = self.cam.read()
        else:
            rval = False

        while rval:
            cv2.imshow(previewName, frame)
            rval, frame = self.cam.read()
            key = cv2.waitKey(20)
            if key == 27:  # exit on ESC
                break
        cv2.destroyWindow(previewName)

class ImageStitcher():
    def __init__(self, sharedMems) -> None:
        self.mode = cv2.Stitcher_PANORAMA
        self.sharedMems = sharedMems
        self.result = None

    def stitch(self):
        imageArray = list()

        for buffer in self.sharedMems:
            if (not buffer.empty()):
                imageArray.append(buffer.get())

        try:
            stitchy = cv2.createStitcher(try_use_gpu=True)
            (status, self.result) = stitchy.stitch(imageArray)
            if (status == 0):
                # all okay here
                return True
            elif (status == 1):
                raise Exception("Error stitching: Not enough keypoints")
            elif (status == 2):
                raise Exception("Error stitching: Homography fail")
        except Exception as e:
            self.result = None
            # print(e)
            
    def showImage(self):
        status = self.stitch()
        if (status):
            cv2.imshow("output", self.result)
            cv2.waitKey(10)
        # time.sleep(3)

def func(camObject):
    camObject.run()
    # camObject.singleThreadGetFrame()


def imageProcessing(shareMems):
    stitcher = ImageStitcher(shareMems)
    while True:
        stitcher.showImage()

def singleThreadTest():
    thread1 = camThread("Camera 0", 0)
    thread2 = camThread("Camera 1", 1)
    while True:
        imageArray = list()

        imageArray.append(thread1.singleThreadGetFrame())
        imageArray.append(thread2.singleThreadGetFrame())

        cv2.imshow("image1", imageArray[0])
        cv2.imshow("image2", imageArray[1])

        stitchy = cv2.createStitcher()
        (status,result) = stitchy.stitch(imageArray)
        if (status == 0):
            cv2.imshow("output", result)
            cv2.waitKey(10)
        else:
            print("issue")
        

if (__name__ == "__main__"):
    # Single threaded test works
    # cameras are not synced
    # singleThreadTest()
    # os.system("taskset -p -c 0,1,2 {}".format(os.getpid()))
    # Create shared memory to store frame
    shareMem1 = multiprocessing.SimpleQueue()
    shareMem2 = multiprocessing.SimpleQueue()

    # Create two threads as follows
    thread1 = camThread("Camera 0", 0, shareMem1)
    thread2 = camThread("Camera 1", 1, shareMem2)
    
    q = multiprocessing.Queue()
    multiprocessing.Process(target=func,args=(thread1,)).start()
    multiprocessing.Process(target=func,args=(thread2,)).start()
    multiprocessing.Process(target=imageProcessing,args=([shareMem1,shareMem2],)).start()
    print("number of CPU", multiprocessing.cpu_count())
    print("Active threads", threading.activeCount())