import cv2
cap0 = cv2.VideoCapture(0)
ret0, frame0 = cap0.read()

cap1 = cv2.VideoCapture(1)
ret1, frame1 = cap1.read()
cv2.imshow("another",frame1)
cv2.imshow("name",frame0)
cv2.waitKey()