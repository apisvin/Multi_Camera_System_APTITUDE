import cv2
import numpy as np
from calib3d import Point3D, Point2D
import time
import logging
from agent.output.bboxes_2d import *
from agent.agent import Agent
from calibration.calibrate import find_calib
import csv
import threading
from filterpy.kalman import KalmanFilter



class kalman():
    
    def __init__(self):
        self.time = 0
        self.dt = 0.2                                   #interval of time between 2 observations
        self.KF = KalmanFilter(dim_x=4, dim_z=2)        #Kalman filter from filterpy 
        self.KF.x = np.array([0., 0., 0., 0.])          # initial state (location, velocity)
        self.KF.F = np.array([[1.,0., self.dt, 0.],
                                [0.,1., 0., self.dt],
                                [0.,0., 1., 0.],
                                [0.,0., 0., 1.]])       # state transition matrix
        self.KF.H = np.array([[1.,0., 0., 0.],
                                [0.,1., 0., 0.]])       # Measurement function (only position)
        self.KF.P *= 30.                                # covariance matrix (already define as np.eye(dim_x))
        self.KF.R = np.array([[1.,0.],
                                [0., 1.]])              # state uncertainty
        self.KF.Q = np.eye(4)*0.1
        self.state = self.KF.x                          # state of the traget
        self.estimate = []
             
    def process_kalman(self, x, y, time):
        if time==0: #first observation
            self.time=time
            self.KF.x = np.array([x, y, 0., 0.]) #initial state
        else:
            self.dt = time-self.time
            self.KF.F = np.array([[1.,0., self.dt, 0.],
                                [0.,1., 0., self.dt],
                                [0.,0., 1., 0.],
                                [0.,0., 0., 1.]])
            self.KF.Q = np.eye(4)*self.dt
            self.KF.predict()
            obs = np.array([x, y])
            self.KF.update(obs)
            self.time = time
        return [self.KF.x[0], self.KF.x[1]]

    def get_estimate(self):
        return np.array(self.estimate)

class decentralized(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue, display=True):
        """
        Detector is a detection agent. It has to process the video from camera in real time 
        or from a video file. It detects Aruco marker and return their coordinate at each frame in a
        global referential. The camera has to be calibrated.
        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
            folder : absolute path to the folder containing :
                                    the video file to read 
                                    the image calibration corresponding to this video
                                    the time_video (.csv) containg the time stamp of each frame 
            t_b : time in seconds since epoch when the benchmark is launched
            display : boolean for displaying in a window the current video (in real time from camera or from video)
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.neighbourhood = neighbourhood
        self.display = display
        self.local_KF = kalman()
        self.global_KF = kalman()
        
    def launch(self):
        threading.Thread(target=self.detection_localKF, args=()).start()
        threading.Thread(target=self.globalKF, args=()).start()



    def detection_localKF(self):
        #create calib class from calibration image 
        image = cv2.imread('../../local_data/image_calibration.png')
        aruco_3D = np.array([[0.,0.,0.],
                        [100.,0.,0.],
                        [0.,100.,0.],
                        [-100.,0.,0.],
                        [0.,-100.,0.],
                        [100.,100.,0.],
                        [-100.,100.,0.],
                        [-100.,-100.,0.],
                        [100.,-100.,0.]], dtype='float32')
        ids_3D = np.array([0,10,12,14,16,18,20,22,24])
        (calib, _) = find_calib(image, aruco_3D, ids_3D, nb_aruco=9, verbose=False)


        # Sizing frames
        width = 1920
        height = 1088
        cap = cv2.VideoCapture(-1)
        if not cap.isOpened():
            logging.warning("Capture object not initialized correctly")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if self.display:
            cv2.namedWindow("result", cv2.WINDOW_FULLSCREEN)
        
        Zoffset = 10
        #aruco parameters
        arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
        arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels
        #begin loop 
        ret, frame = cap.read()
        start = time.time()
        while ret==True and self.stopFlag.is_set()==False:
            ##################################################Detection step
            #ArUco marker detection from frame
            (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict,parameters=arucoParams)
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
                    corners2D = markerCorner.reshape((4, 2))
                    #corners2D = (topLeft, topRight, bottomRight, bottomLeft)
                    
                    #get center of aruco marker
                    center_pos_x = (corners2D[0][0]+corners2D[1][0]+corners2D[2][0]+corners2D[3][0])/4
                    center_pos_y = (corners2D[0][1]+corners2D[1][1]+corners2D[2][1]+corners2D[3][1])/4
                            

                    #draw detection point on 2D frame
                    i+=1
                    position = (int(center_pos_x), int(center_pos_y))
                    positionText = (int(center_pos_x), int(center_pos_y)-15)
                    cv2.circle(frame, position, 12, (0, 0, 255), -1)
                    cv2.putText(frame, "Object_aruco_"+str(i), positionText, cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA) 
                
                    # dictionnary for detected object
                    point3D = calib.project_2D_to_3D(Point2D(int(center_pos_x), int(center_pos_y)), Z = Zoffset)
                    objectID = int(markerID)
                    classID = "aruco"
                    position = {"x" : float(point3D.x),
                                "y" : float(point3D.y),
                                "z" : float(point3D.z)}
                    detobject = {"objectID" : objectID,
                                 "classID" : classID,
                                 "position" : position,
                                 "time" : time.time()}
                    objects.append(detobject)

            ####################################################Local Kalman
            if(len(objects)>0):
                for o in objects:
                    #perform local kalman filter
                    local_x, local_y = self.local_KF.process_kalman(float(o["position"]["x"]), float(o["position"]["y"]), float(o["time"]))
                    #send prediction from local KF to global kalman filter
                    msg = {"source" : self.neighbourhood.myself.__dict__,
                        "destination" : "my_globalKF",
                        "method" : "localKF",
                        "spec" : {"local_x" : local_x,
                                        "local_y" : local_y, 
                                        "local_time" : float(o["time"])}}
                    self.dicqueue.QtoglobalKF.put(msg)
                    #send prediction from local KF to all neighbour's global kalman filter
                    for neighbour in self.neighbourhood.get_all_neighbours():
                        msg = {"source" : self.neighbourhood.myself.__dict__,
                        "destination" : neighbour.__dict__,
                        "method" : "localKF",
                        "spec" : {"local_x" : local_x,
                                        "local_y" : local_y, 
                                        "local_time" : float(o["time"])}}
                        self.dicqueue.Qtosendunicast.put(msg)
            
            ####################################################Display video
            if self.display:
                frameResized = cv2.resize(frame, (960,540))
                cv2.imshow("result", frameResized)
                cv2.waitKey(1)


            ##################################################capture new frame
            ret, frame = cap.read()
            
        logging.debug("total time of detector offline = {} s".format(time.time()-start))
        cap.release()
        cv2.destroyWindow("result")


    def globalKF(self):
        while self.stopFlag.is_set()==False:
            #################################################Process global kalman with local estimates
            msg = self.dicqueue.QtoglobalKF.get()
            local_x = msg["spec"]["local_x"]
            local_y = msg["spec"]["local_y"]
            local_time = msg["spec"]["local_time"]
            global_x, global_y = self.global_KF.process_kalman(local_x, local_y, local_time)

            #################################################Send global estimate to car 
            msg = {"x" : global_x,
                    "y" : global_y}
            logging.debug("car localisation is : {}".format(msg))
                            

