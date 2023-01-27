from PIL import Image
import io
from os import getcwd
from os.path import join
import cv2
import numpy as np

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
		self._mode = cv2.Stitcher_PANORAMA
		self._cameras = imageCVArray
		self._imageArray = list()
		self._result = None
		self._imageCount = 0
		
	def _stitch(self):
		try:
			for item in self._cameras:
				self._imageArray.append(item.getCVImage())
			stitchy = cv2.createStitcher(self._mode)
			(status, self._result) = stitchy.stitch(self._imageArray)
			if (status == 0):
				# all okay here
				return True
			elif (status == 1):
				raise Exception("Error stitching: Not enough keypoints")
			elif (status == 2):
				raise Exception("Error stitching: Homography fail")
		except Exception as e:
			print(e)
			# raise e
		
	def stitch(self, imageArray=None):
		if (imageArray==None):
			try:
				return self._stitch()
			except Exception as e:
				print(e)
		else:
			try:
				self._imageArray = imageArray
				stitchy = cv2.createStitcher(self._mode)
				(status, self._result) = stitchy.stitch(self._imageArray)
				if (status == 0):
					# all okay here
					return True
				elif (status == 1):
					# cv2.imshow("image1", self._imageArray[0])
					# cv2.waitKey(0)
					# cv2.imshow("image2", self._imageArray[1])
					# cv2.waitKey(0)
					raise Exception("Error stitching: Not enough keypoints")
				elif (status == 2):
					raise Exception("Error stitching: Homography fail")
			except Exception as e:
				print(e)

	# def _showImage(self):
	# 	if (self.stitch()):
	# 		cv2.imshow("image1", self._imageArray[0])
	# 		cv2.imshow("image2", self._imageArray[1])
	# 		cv2.imshow("output", self._result)
	# 		cv2.waitKey(100)

	def showImage(self, imageArray=None, saveImage=True):
		if (imageArray==None):
			result = self.stitch()
		else:
			result = self.stitch(imageArray)
	
		if (result):
			cv2.imshow("image1", self._imageArray[0])
			cv2.imshow("image2", self._imageArray[1])
			cv2.imshow("output", self._result)
			cv2.waitKey(100)

			if (saveImage): self.saveImage()

		
   
	def saveImage(self, all=True, dir=getcwd()):
		if (all):
			cv2.imwrite(join(dir,"..","imageDir",'stitch_{}.jpg'.format(self._imageCount)), self._result)
			cv2.imwrite(join(dir,"..","imageDir",'left_{}.jpg'.format(self._imageCount)), self._imageArray[0])
			cv2.imwrite(join(dir,"..","imageDir",'right_{}.jpg'.format(self._imageCount)), self._imageArray[1])
		else:
			cv2.imwrite(join(dir,"..","imageDir",'stitch_{}.jpg'.format(self._imageCount)), self._result)
		self._imageCount += 1