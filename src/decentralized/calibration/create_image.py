import cv2
from calib3d import Point3D, Point2D
from matplotlib import pyplot as plt
import time
import logging

width = 1920
height = 1088

# Sizing frames
cap = cv2.VideoCapture(-1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

ret, frame = cap.read()
time.sleep(1)
ret, frame = cap.read()
cv2.imwrite("/home/pi/Multi_Camera_System_APTITUDE/local_data/image_calibration.png",frame)
