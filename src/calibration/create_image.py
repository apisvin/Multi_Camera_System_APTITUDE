import cv2
import numpy as np
from calib3d import Point3D, Point2D
import uuid
from matplotlib import pyplot as plt
import time
import sys
import logging

width = 1920
height = 1088

# Sizing frames
cap = cv2.VideoCapture(-1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

#time.sleep(3)
# Loop for detection
ret, frame = cap.read()
time.sleep(1)
ret, frame = cap.read()
cv2.imwrite("image_calibration.png",frame)
