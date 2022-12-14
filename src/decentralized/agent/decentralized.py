import cv2
import numpy as np
from calib3d import Point3D, Point2D
import time
import logging
from agent.agent import Agent
from calibration.calibrate import find_calib
import csv
import threading
from filterpy.kalman import KalmanFilter
from pytb.detection.detection_manager import DetectionManager
from pytb.detection.detector_factory import DetectorFactory
from pytb.tracking.tracker_factory import TrackerFactory
from  pytb.tracking.tracking_manager import TrackingManager


class kalman():
    
    def __init__(self, dim_x=4, dim_z=2, dim_u=0):
        """Asynchronnous decentralized kalman filter"""
        if dim_x < 1:
            raise ValueError('dim_x must be 1 or greater')
        if dim_z < 1:
            raise ValueError('dim_z must be 1 or greater')
        if dim_u < 0:
            raise ValueError('dim_u must be 0 or greater')

        self.dim_x = dim_x
        self.dim_z = dim_z
        self.dim_u = dim_u


        self.x = np.zeros((dim_x, 1))        # state
        self.P = np.eye(dim_x)               # uncertainty covariance
        self.Q = np.eye(dim_x)               # process uncertainty
        self.F = np.eye(dim_x)               # state transition matrix
        self.H = np.zeros((dim_z, dim_x))    # Measurement function
        self.R = np.eye(dim_z)               # state uncertainty
        self.M = np.zeros((dim_z, dim_z)) # process-measurement cross correlation
        self.z = np.array([[None]*self.dim_z]).T

        # gain and residual are computed during the innovation step. We
        # save them so that in case you want to inspect them for various
        # purposes
        self.W = np.zeros((dim_x, dim_z)) # kalman gain
        self.y = np.zeros((dim_z, 1))
        self.S = np.zeros((dim_z, dim_z)) # system uncertainty
        self.SI = np.zeros((dim_z, dim_z)) # inverse system uncertainty

        # identity matrix. Do not alter this.
        self._I = np.eye(dim_x)

        # these will always be a copy of x,P after predict() is called
        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

        # these will always be a copy of x,P after update() is called
        self.x_post = self.x.copy()
        self.P_post = self.P.copy()

        self.inv = np.linalg.inv

        # time variable 
        self.t = 0          # time derived from internal clock when a measurement is received
        self.tau = 0        # time of the last update()


    def predict(self):
        """
        Predict next state (prior) using the Kalman filter state propagation
        equations.
        """
        
        # compute transition matrix F 
        self.t = time.time()
        self.dt = self.t - self.tau
        self.F = np.array([[1.,0., self.dt, 0.],
                            [0.,1., 0., self.dt],
                            [0.,0., 1., 0.],
                            [0.,0., 0., 1.]])       # state transition matrix

        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        self.x_prior = self.x.copy()
        self.P_prior = self.P.copy()

    def update(self, z):
        """
        Add a new measurement (z) to the Kalman filter.
        """
        self.y = z - np.dot(self.H, self.x_prior)      #error (residual) between measurement and prediction
        
        Pinv = self.inv(self.P) + np.dot(self.H.T, np.dot(self.inv(self.R), self.H))
        self.P = self.inv(Pinv)
        #kalman gain computation
        self.W = np.dot(self.P, np.dot(self.H.T, self.inv(self.R)))

        self.x = self.x_prior + np.dot(self.W, self.y)
        self.tau = time.time() #time of last update

        self.x_post = self.x.copy()
        self.P_post = self.P.copy()


    def assimilation(self, VEI, SEI):
        """
        Assimilation of the VEI (Variance Error Info) and the SEI (State Error Info) from node j 
        A prediction step is done before
        """

        Pinv = self.inv(self.P_prior) + VEI
        self.P = self.inv(Pinv)

        self.x = np.dot(self.P, np.dot(self.inv(self.P_prior), self.x_prior) + SEI)


    def get_error_info(self, z):
        """
        return State Error Info and Variance Error Info to send to other nodes
        """
        SEI = np.dot(self.H.T, np.dot(self.inv(self.R), z))
        VEI = np.dot(self.H.T, np.dot(self.inv(self.R), self.H))
        return SEI, VEI
        



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
            display : boolean for displaying in a window the current video (in real time from camera or from video)
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.neighbourhood = neighbourhood
        self.display = display
        self.distributed_KF = kalman()
        self.distributed_KF.H = np.array([[1.,0., 0., 0.],
                                            [0.,1., 0., 0.]])       # Measurement function (only position)
        
    def launch(self):
        threading.Thread(target=self.detection, args=()).start()
        threading.Thread(target=self.globalKF, args=()).start()



    def detection(self):
        #create calib class from calibration image 
        image = cv2.imread('src/image_calibration.png')
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

        #initializing detector 
        config_aruco = {
                "proc":{
                    "task": "detection",
                    "output_type": "bboxes2D",
                    "model_type": "Aruco",
                    "pref_implem": "Aruco",
                    "params": {
                    }
                },
                "preproc":{
                    "resize":{
                        "width" : 416,
                        "height": 416
                    }
                },
                "postproc":{
                    "nms": {
                        "pref_implem" : "Malisiewicz",
                        "nms_thresh" : 0.45
                    }
                }
            }
        detect1_proc = config_aruco['proc']
        detect1_preproc = config_aruco['preproc']
        detect1_postproc = config_aruco['postproc']

        # Instantiate the detector
        detection_manager = DetectionManager(DetectorFactory.create_detector(detect1_proc), detect1_preproc,
                                            detect1_postproc)


        # Sizing frames
        width = 1920
        height = 1088
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.warning("Capture object not initialized correctly")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if self.display:
            cv2.namedWindow("result", cv2.WINDOW_FULLSCREEN)
        
        Zoffset = 18
        #begin loop 
        ret, frame = cap.read()
        start = time.time()
        while ret==True and self.stopFlag.is_set()==False:
            ####################################################detection in camera coordinate 
            det = detection_manager.detect(frame)
            det.change_dims(width, height)
            det.to_x1_y1_x2_y2()
            det_time = time.time()

            #####################################################local Kalman filter
            objects = []
            for bb, class_ID in zip(det.bboxes, det.class_IDs):
                if class_ID == 0: #detected object is the car -> need tracking 
                    center_pos_x = (bb[0]+bb[2])/2
                    center_pos_y = (bb[1]+bb[3])/2
                    #tranformation to global coordinate
                    point3D = calib.project_2D_to_3D(Point2D(int(center_pos_x), int(center_pos_y)), Z = Zoffset)
                    z = np.array([[point3D.x], [point3D.y]])
                    
                    #send observation to decentralized kalman filter
                    msg = {"source" : self.neighbourhood.myself.__dict__,
                            "destination" : "my_KF",
                            "method" : "detection",
                            "spec" : {"local_x" : z[0],
                                        "local_y" : z[1], 
                                        "class_ID" : str(class_ID)}}
                    self.dicqueue.QtoglobalKF.put(msg)
                    
                else: #detected object is an obstacle -> no need tracking, only detection
                    for car in self.neighbourhood.get_cars():
                        center_pos_x = (bb[0]+bb[2])/2
                        center_pos_y = (bb[1]+bb[3])/2
                        point3D = calib.project_2D_to_3D(Point2D(int(center_pos_x), int(center_pos_y)), Z = Zoffset)
                        msg = {"source" : self.neighbourhood.myself.__dict__,
                                "destination" : car.__dict__,
                                "method" : "positionCar",
                                "spec" : {"x" : float(point3D.x),
                                           "y" : float(point3D.y),
                                           "class_ID" : str(class_ID)}}
                        
                        self.dicqueue.Qtosendunicast.put(msg)
                    
            
            ####################################################Display video
            if self.display:
                for bb, class_ID in zip(det.bboxes, det.class_IDs):
                    cv2.rectangle(frame, (bb[0], bb[1]), (bb[2], bb[3]),(0, 0, 255), 12)
                    # Write a text with the vehicle label, the confidence score and the ID
                    cv2.putText(frame, str(class_ID), (bb[0], bb[1]), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

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
            msg = self.dicqueue.QtoglobalKF.get()

            if msg["destination"] == "my_KF":
                #perform kalman filter with its own measurements
                self.distributed_KF.predict()
                z = np.array([[float(msg["spec"]["local_x"])], [float(msg["spec"]["local_y"])]])
                self.distributed_KF.update(z)
                print(self.distributed_KF.x)

                #communicate state error info and variance error info to all other neighbours
                SEI, VEI = self.distributed_KF.get_error_info(z)
                for neighbour in self.neighbourhood.get_all_neighbours():
                    msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : neighbour.__dict__,
                    "method" : "ErrorInfo",
                    "spec" : {"SEI" : SEI,
                                "VEI" : VEI, 
                                "state" : self.distributed_KF.x}}
                    self.dicqueue.Qtosendunicast.put(msg)

            #################################################get error info from other nodes
            else:
                state = msg["spec"]["state"]
                SEI = msg["spec"]["SEI"]
                VEI = msg["spec"]["VEI"]
                #TODO: association based on state if multiple tragets
                self.distributed_KF.assimilation(VEI, SEI)
