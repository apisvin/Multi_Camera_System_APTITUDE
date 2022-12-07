import cv2
import numpy as np
from calib3d import Point3D, Point2D
import time
import logging
from agent.agent import Agent
import csv
import threading
from filterpy.kalman import KalmanFilter

class car(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        Detector is a detection agent. It has to process the video from camera in real time 
        or from a video file. It detects Aruco marker and return their coordinate at each frame in a
        global referential. The camera has to be calibrated.
        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.neighbourhood = neighbourhood
        
    def launch(self):
        #INSERT HERE CODE OF CAR
        while self.stopFlag.is_set()==False:
            msg = self.dicqueue.get()
            print(msg)


