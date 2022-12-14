import cv2
import numpy as np
from calib3d import Point3D, Point2D
import time
import logging
from agent.output.bboxes_2d import *
from agent.agent import Agent


class Detector(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue, calib, display=False):
        """
        Detector is a detection agent. It has to process the video from camera in real time 
        or from a video file. It detects Aruco marker and return their coordinate at each frame in a
        global referential. The camera has to be calibrated.
        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
            calib : Calib class contains information about the positioning of the camera in space in a global referential.
                    This class is used to tranform 2D coordinate in the plane of the camera frame to 3D coordinate in the global referential.
            display : boolean for displaying in a window the current video (in real time from camera or from video)
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.neighbourhood = neighbourhood
        self.calib = calib
        self.display = display
        self.fps = 1
        
    def launch(self):
        """
        Launch the detection loop. It reads the camera video flux or video file. Then, it detects aruco markers 
        and tranform their 2D coordinates in the plane of the image into 3D coordinates of the global frame.
        Finally, its sends all its detections to its parent if it has one.
        """
        # Sizing frames
        width = 1920
        height = 1088
        cap = cv2.VideoCapture(-1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        #cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        #set buffersize to display without delay
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        cv2.namedWindow("frame", cv2.WINDOW_FULLSCREEN)
        
        Zoffset = 0
        # Loop for detection
        ret, frame = cap.read()
        time.sleep(0.001)
        ret, frame = cap.read()
        arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels
        while ret==True and self.stopFlag.is_set()==False:
            
            #capture image
            ret, frame = cap.read()
            if ret == True:
                start = time.time()
                
                #ArUco marker def
                arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
                (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict,parameters=arucoParams)
                            
                #corners: A list containing the (x, y)-coordinates of our detected ArUco markers
                #ids : The ArUco IDs of the detected markers
                
                #buffer to keep all objects 
                objects = []
                bboxes = []
                classIDs = []
                i=0
                
                #ArUco detection
                if(ids is not None):
                    ids = ids.flatten()
                    for (markerCorner, markerID) in zip(corners, ids):
                        # extract the marker corners (which are always returned in
                        # top-left, top-right, bottom-right, and bottom-left order)
                        corners2D = markerCorner.reshape((4, 2))
                        #(topLeft, topRight, bottomRight, bottomLeft) = corners
                        x3D = []
                        y3D = []
                        for corner2D in corners2D:
                            corner3D = self.calib.project_2D_to_3D(Point2D(int(corner2D[0]), int(corner2D[1])), Z = 8)
                            x3D.append(corner3D.x)
                            y3D.append(corner3D.y)

                        """
                        topLeft3D = self.calib.project_2D_to_3D(Point2D(int(corners2D[0][0]), int(corners2D[0][1])), Z = 0)
                        topRight3D = self.calib.project_2D_to_3D(Point2D(int(corners2D[1][0]), int(corners2D[1][1])), Z = 0)
                        bottomLeft3D = self.calib.project_2D_to_3D(Point2D(int(corners2D[2][0]), int(corners2D[2][1])), Z = 0)
                        bottomRight3D = self.calib.project_2D_to_3D(Point2D(int(corners2D[3][0]), int(corners2D[3][1])), Z = 0)
                        """
                        """
                        #create bounding box on 3D frame 
                        x = int(min(x3D))
                        y = int(min(y3D))
                        w = int(max(y3D) - y)
                        h = int(max(x3D) - x)
                        #draw bouning box on 2D frame
                        pt1 = self.calib.project_3D_to_2D(Point3D(x, y, 0))
                        pt1 = [int(pt1.x), int(pt1.y)]
                        pt2 = self.calib.project_3D_to_2D(Point3D(x+w, y, 0))
                        pt2 = [int(pt2.x), int(pt2.y)]
                        pt3 = self.calib.project_3D_to_2D(Point3D(x+w, y+h, 0))
                        pt3 = [int(pt3.x), int(pt3.y)]
                        pt4 = self.calib.project_3D_to_2D(Point3D(x, y+h, 0))
                        pt4 = [int(pt4.x), int(pt4.y)]
                        pts = np.array([pt1,pt2,pt3,pt4], np.int32)
                        pts = pts.reshape((-1, 1, 2))
                        cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
                        #project bbox on the ground
                        bboxes.append([x,y,w,h])
                        classIDs.append(markerID)
                        """
                        #draw detection point on 2D frame
                        i+=1
                        position = (int(corners2D[0][0]), int(corners2D[0][1]))
                        positionText = (int(corners2D[0][0]), int(corners2D[0][1])-15)
                        cv2.circle(frame, position, 12, (0, 0, 255), -1)
                        cv2.putText(frame, "Object_aruco_"+str(i), positionText, cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA) 
                    
                        

                        # dictionnary for detected object
                        point3D = self.calib.project_2D_to_3D(Point2D(int(corners2D[0][0]), int(corners2D[0][1])), Z = Zoffset)
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
                
                
                if(len(objects)>0 and self.neighbourhood.parent != 0):
                    end = time.time()
                    """
                    BBoxes = BBoxes2D(end-start, np.array(bboxes), np.array(classIDs), np.ones(len(bboxes)), frame.shape[1], frame.shape[0])
                    # dictionnary for msg to send
                    msg = {"source" : "",
                           "destination" : "",
                           "method" : "detect",
                           "spec" : {"BBoxes2D" : BBoxes}}"""
                    msg = {"source" : self.neighbourhood.myself.__dict__,
                           "destination" : self.neighbourhood.parent.__dict__,
                           "method" : "detect",
                           "spec" : {"objects" : objects}}
                    self.dicqueue.Qtosendunicast.put(msg)
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
    

