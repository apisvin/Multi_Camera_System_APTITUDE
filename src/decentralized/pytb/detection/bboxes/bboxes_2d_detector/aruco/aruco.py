from pytb.detection.bboxes.bboxes_2d_detector.bboxes_2d_detector import BBoxes2DDetector
from pytb.output.bboxes_2d import BBoxes2D

from timeit import default_timer
import cv2
import numpy as np
import logging

log = logging.getLogger("aptitude-toolbox")

class Aruco(BBoxes2DDetector):

    def __init__(self, proc_parameters: dict):
        """Initializes the detector with the given parameters.

        Args:
            proc_parameters (dict): A dictionary containing the BackgroundSubstractor detector parameters
        """
        super().__init__(proc_parameters)

        log.debug("ArucoDetector {} implementation selected.".format(self.pref_implem))
        self.arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
        self.arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels



    def detect(self, frame: np.array) -> BBoxes2D:
        start = default_timer()
        #ArUco marker detection from frame
        (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, self.arucoDict,parameters=self.arucoParams)
        #corners: A list containing the (x, y)-coordinates of our detected ArUco markers
        #ids : The ArUco IDs of the detected markers

        bboxes = []
        class_IDs = []
        #ArUco detection
        if(ids is not None):
            ids = ids.flatten()
            for (markerCorner, markerID) in zip(corners, ids):
                # extract the marker corners (which are always returned in
                # top-left, top-right, bottom-right, and bottom-left order)
                corners2D = markerCorner.reshape((4, 2))
                #corners2D = (topLeft, topRight, bottomRight, bottomLeft)
                x, y, w, h = cv2.boundingRect(corners2D)
                
                bboxes.append([x, y, w, h])
                class_IDs.append(markerID)
                
        end = default_timer()

        return BBoxes2D(end-start, np.array(bboxes), np.array(class_IDs).astype(int),
                    np.ones(len(bboxes)), frame.shape[1], frame.shape[0])