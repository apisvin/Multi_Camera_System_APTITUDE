import cv2
import numpy as np
from calib3d import Point3D, Point2D
import uuid
from matplotlib import pyplot as plt
import time
import sys
import logging
from agent.output.bboxes_2d import *



class detection:
    """
    detection is used by detection agent. The hardware must be equipped
    with a camera and opencv
    """
    
    def __init__(self, stopFlag, calib, dicqueue, display=False):
        """
        stopFlag : flag to stop executing thread 
        dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.calib = calib
        self.display = display
        self.fps = 1
        
    def launch(self):
        """ 
        Une phase de calibration est necessaire
        """
        
        width = 1920
        height = 1088
        
        # Sizing frames
        cap = cv2.VideoCapture(-1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        #set buffersize to display without delay
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        cv2.namedWindow("frame", cv2.WINDOW_FULLSCREEN)
        
        #time.sleep(3)
        # Loop for detection
        ret, frame = cap.read()
        time.sleep(0.001)
        ret, frame = cap.read()
        arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels
        logging.debug("launch detection")
        while ret==True and self.stopFlag.is_set()==False:
            
            #capture image
            ret, frame = cap.read()
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # Conversion RGB to HSV
            image = cv2.blur(image, (5, 5)) # Blur the image to expand the pixel 

            start = time.time()
            
            #ArUco marker def
            arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
            (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict,parameters=arucoParams)

            end = time.time()
                        
            #corners: A list containing the (x, y)-coordinates of our detected ArUco markers
            #ids : The ArUco IDs of the detected markers
            
            #buffer to keep all objects 
            objects = []
            i=0
            
            #ArUco detection
            if(ids is not None):
                ids = ids.flatten()
                for (markerCorner, markerID) in zip(corners, ids):
                    # extract the marker corners (which are always returned in
                    # top-left, top-right, bottom-right, and bottom-left order)
                    corners = markerCorner.reshape((4, 2))
                    #(topLeft, topRight, bottomRight, bottomLeft) = corners
                    #draw detection point on frame
                    i+=1
                    position = (int(corners[0][0]), int(corners[0][1]))
                    positionText = (int(corners[0][0]), int(corners[0][1])-15)
                    cv2.circle(frame, position, 12, (0, 0, 255), -1)
                    cv2.putText(frame, "Object_aruco_"+str(i), positionText, cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA) 

                    #create bounding box on frame 
                    x = min(corners[:,0])
                    y = min(corners[:,1])
                    w = max(corners[:,1]) - y
                    h = max(corners[:,0]) - x
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 0, 255), 2)
                
                    point3D = self.calib.project_2D_to_3D(Point2D(int(corners[0][0]), int(corners[0][1])), Z = 0)

                    # dictionnary for detected object
                    objectID = int(markerID)
                    classID = "aruco"
                    position = {"x" : float(point3D.x),
                                "y" : float(point3D.y),
                                "z" : float(point3D.z)}
                    velocity = {"x'" : 0.0,
                                "y'" : 0.0,
                                "z'" : 0.0}
                    bbox = {"w" : 0,
                            "h" : 0,
                            "bboxFormat" : "rectangle",
                            "confInt" : 0.0}
                    detobject = {"objectID" : objectID,
                                 "classID" : classID,
                                 "position" : position,
                                 "velocity" : velocity,
                                 "bbox" : bbox}
                    objects.append(detobject)
            
            
            if(len(objects)>0):
                # dictionnary for msg to send
                msg = {"source" : "",
                       "destination" : "",
                       "method" : "detect",
                       "spec" : {"numbersObjects" : len(objects),
                                 "objects" : objects}}
                self.dicqueue.Qtoidentification.put(msg)
            ####################################################
            if self.display:
                frameResized = cv2.resize(frame, (960,540))
                cv2.imshow("frame", frameResized)
            
            cv2.waitKey(self.fps) 
            
                    
            # Break the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            

        cap.release()
        cv2.destroyAllWindows()
    

