from PIL import Image
import io
from os import getcwd
from os.path import join
import cv2
import imutils
import numpy as np
from multiprocessing import Process
from typing import List

class ImageCV:
    def __init__(self, gstSample=None):
        if (gstSample == None):
            return
        self._imageBuffer = self.getImageBuffer(gstSample)
        self._image = Image.open(io.BytesIO(self._imageBuffer))
        self._imageCV = None
        self.toOpenCV()

    def getImageBuffer(self,gstSample):
        if gstSample is None:
            return None
        
        # get buffer from the Gst.sample object
        buf = gstSample.get_buffer()
        buf2 = buf.extract_dup(0, buf.get_size())
        return buf2
    
    def updateCVImage(self,gstSample):
        self._imageBuffer = self.getImageBuffer(gstSample)
        imageStream = io.BytesIO(self._imageBuffer)
        self._imageCV = cv2.imdecode(np.frombuffer(imageStream.read(), np.uint8), -1)
        return self._imageCV

    def toOpenCV(self):
        imageStream = io.BytesIO(self._imageBuffer)
        self._imageCV = cv2.imdecode(np.frombuffer(imageStream.read(), np.uint8), -1)
        # print(type(self._imageCV))
    
    def showCVImage(self):
        if (self._imageCV is None):
            raise Exception("Image CV not created")
        cv2.imshow("image", self._imageCV)
        cv2.waitKey(100)

    def showPillowImage(self):
        self._image.show()
    
    def getCVImage(self):
        return self._imageCV

from typing import List
class ImageStitcher():
    def __init__(self,imageCVArray:List[ImageCV], size:int=2) -> None:
        self._size = size
        self._cameras = imageCVArray
        self._imageArray = list()
        self._result = None
        self._imageCount = 0

    def stitch(self):
        try:
            stitchy = cv2.createStitcher() 
            (status, self._result) = stitchy.stitch(self._imageArray)
            if (status == 0):
                # all okay here
                self.saveImage()
                return True
            elif (status == 1):
                raise Exception("Error stitching: Not enough keypoints")
            elif (status == 2):
                raise Exception("Error stitching: Homography fail")
        except Exception as e:
            print(e)

    # Refernce:
    # https://colab.research.google.com/drive/11Md7HWh2ZV6_g3iCYSUw76VNr4HzxcX5#scrollTo=6eHgWAorE9gf
    # https://towardsdatascience.com/image-panorama-stitching-with-opencv-2402bde6b46c	
    # Image stitching speed is approximately 3 frames per second with this improved method
    def detectAndDescribe(self, image, method='orb'):
        """
        Compute key points and feature descriptors using an specific method
        """
        assert method is not None, "You need to define a feature detection method. Values are: 'sift', 'surf'"

        # detect and extract features from the image
        if method == 'sift':
            descriptor = cv2.xfeatures2d.SIFT_create()
        elif method == 'surf':
            descriptor = cv2.xfeatures2d.SURF_create()
        elif method == 'brisk':
            descriptor = cv2.BRISK_create()
        elif method == 'orb':
            descriptor = cv2.ORB_create(nfeatures=2000)
        # get keypoints and descriptors
        (kps, features) = descriptor.detectAndCompute(image, None)
        return (kps, features)
    
    def createMatcher(self, method,crossCheck):
        "Create and return a Matcher Object"
        if method == 'sift' or method == 'surf':
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
        elif method == 'orb' or method == 'brisk':
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=crossCheck)
        return bf
    def matchKeyPointsBF(self, featuresA, featuresB, method='orb'):
        bf = self.createMatcher(method, crossCheck=True)
        # Match descriptors.
        best_matches = bf.match(featuresA,featuresB)
        # Sort the features in order of distance.
        # The points with small distance (more similarity) are ordered first in the vector
        rawMatches = sorted(best_matches, key = lambda x:x.distance)
        print("Raw matches (Brute force):", len(rawMatches))
        return rawMatches
    
    def matchKeyPointsKNN(self, featuresA, featuresB, ratio=0.75, method='orb'):
        bf = self.createMatcher(method, crossCheck=False)
        # compute the raw matches and initialize the list of actual matches
        rawMatches = bf.knnMatch(featuresA, featuresB, 2)
        print("Raw matches (knn):", len(rawMatches))
        matches = []

        # loop over the raw matches
        for m,n in rawMatches:
            # ensure the distance is within a certain ratio of each
            # other (i.e. Lowe's ratio test)
            if m.distance < n.distance * ratio:
                matches.append(m)
        return matches
    def getHomography(self, kpsA, kpsB, featuresA, featuresB, matches, reprojThresh):
        # convert the keypoints to numpy arrays
        kpsA = np.float32([kp.pt for kp in kpsA])
        kpsB = np.float32([kp.pt for kp in kpsB])
        if len(matches) > 4:
            # construct the two sets of points
            ptsA = np.float32([kpsA[m.queryIdx] for m in matches])
            ptsB = np.float32([kpsB[m.trainIdx] for m in matches])
            # estimate the homography between the sets of points
            (H, status) = cv2.findHomography(ptsA, ptsB, cv2.RANSAC,
                reprojThresh)
            return (matches, H, status)
        else:
            return None
    def homoStitch(self, imageArray=None):
        self._imageArray = imageArray
        if (self._imageArray==None):
            self._imageArray = list()
            for item in self._cameras:
                self._imageArray.append(item.getCVImage())
        kpsA, featuresA = self.detectAndDescribe(self._imageArray[0], method='orb')
        kpsB, featuresB = self.detectAndDescribe(self._imageArray[1], method='orb')
        matches = self.matchKeyPointsBF(featuresA, featuresB, method='orb')
        M = self.getHomography(kpsA, kpsB, featuresA, featuresB, matches, reprojThresh=4)
        if M is None:
            raise Exception("Error getting Homo")
        (matches, H, status) = M
        width = self._imageArray[0].shape[1] + self._imageArray[1].shape[1]
        height = self._imageArray[0].shape[0] + self._imageArray[1].shape[0]

        self._result = cv2.warpPerspective(self._imageArray[0], H, (width, height))
        self._result[0:self._imageArray[1].shape[0], 0:self._imageArray[1].shape[1]] = self._imageArray[1]

        # transform the panorama image to grayscale and threshold it 
        gray = cv2.cvtColor(self._result, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]

        # Finds contours from the binary image
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # get the maximum contour area
        c = max(cnts, key=cv2.contourArea)

        # get a bbox from the contour area
        (x, y, w, h) = cv2.boundingRect(c)

        # crop the image to the bbox coordinates
        self._result = self._result[y:y + h, x:x + w]
        self.saveImage()
    # END OF REFERENCE

    def fast_stitch(self, imageArray:List):
        # Reference: https://github.com/lukasalexanderweber/stitching
        # package unable to stitch image
        self._imageArray = imageArray
        print("hello")
        cv2.imwrite(join(getcwd(),"..","imageDir",'left.jpg'), self._imageArray[0])
        cv2.imwrite(join(getcwd(),"..","imageDir",'right.jpg'), self._imageArray[1])
        stitcher = Stitcher()
        self._result = stitcher.stitch(["../imageDir/left.jpg", "../imageDir/right.jpg"])

    def nextImage(self, imageArray=None, saveImage=True, showImage=False, dir=getcwd()):
        if (type(imageArray) is list):
            self._imageArray = imageArray
        else:
            for item in self._cameras:
                self._imageArray.append(item.getCVImage())
        
        result = self.stitch()
   
        if (showImage and result):
            self.showImage()
        if (saveImage and result):
            self.saveImage(dir=dir)
        
    def showImage(self):
        if (type(self._result) is not np.ndarray):
            return
        cv2.imshow("image1", self._imageArray[0])
        cv2.imshow("image2", self._imageArray[1])
        cv2.imshow("output", self._result)
        cv2.waitKey(100)
        
    def saveImage(self, all=True, dir=getcwd()):
        def worker(location, img):
            # save in grey scale
            # resize with (width, height)
            try:
                if img.shape == (600, 800, 3):
                    cv2.imwrite(location, img[:, :, 1])
                else:
                    # if exception thrown, ignore image frame
                    cv2.imwrite(location, img[:600, :1000, 1])
            except:
                return
            

        if (type(self._result) is not np.ndarray):
            return
        
        self._imageCount = (self._imageCount + 1) %5
        if (all):
            jobs = []
            jobs.append(Process(target=worker, args=(join(dir,"..","imageDir",'stitch{}.jpg'.format(self._imageCount)), self._result)))
            jobs.append(Process(target=worker, args=(join(dir,"..","imageDir",'left{}.jpg'.format(self._imageCount)), self._imageArray[0])))
            jobs.append(Process(target=worker, args=(join(dir,"..","imageDir",'right{}.jpg'.format(self._imageCount)), self._imageArray[1])))
            for process in jobs:
                process.start()
            for process in jobs:
                process.join()
                
            # cv2.imwrite(join(dir,"..","imageDir",'stitch.jpg'), self._result)
            # cv2.imwrite(join(dir,"..","imageDir",'left.jpg'), self._imageArray[0])
            # cv2.imwrite(join(dir,"..","imageDir",'right.jpg'), self._imageArray[1])
        else:
            cv2.imwrite(join(dir,"..","imageDir",'stitch{}.jpg'.format(self._imageCount)), self._result)