import cv2
import numpy as np
from calib3d import Point3D, Point2D
import time
import logging
from agent.output.bboxes_2d import *
from agent.agent import Agent
from calibration.calibrate import find_calib
import csv

class OfflineDetector(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue, folder, t_b, display=True):
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
        if folder == None:
            logging.warning("please give a video path to offline detector")
        self.folder = folder
        self.t_b = t_b
        
    def launch(self):
        """
        Launch the detection loop. It reads the camera video flux or video file. Then, it detects aruco markers 
        and tranform their 2D coordinates in the plane of the image into 3D coordinates of the global frame.
        Finally, its sends all its detections to its parent if it has one.
        """
        #create calib class from calibration image 
        image = cv2.imread(self.folder+'/image_calibration.png')
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
        cap = cv2.VideoCapture(self.folder+"/video.avi")
        if not cap.isOpened():
            logging.warning("please give a valid video path to offline detector")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if self.display:
            cv2.namedWindow(self.folder, cv2.WINDOW_FULLSCREEN)
        
        Zoffset = 10
        # Loop for detection timestamp
        time_video = []
        with open(self.folder+"/time_video.csv", "r")as df_time:
            readerTime = csv.DictReader(df_time)
            for row in readerTime:
                time_video.append(float(row["time"]))
        time_video = np.array(time_video)
        time_reset = time_video-time_video[0] #begin at zero sec
        time_video_now = time_reset+self.t_b #time vector translated now 

        #set frame number depending on delay
        delay = time.time()-self.t_b
        frame_number = np.searchsorted(time_reset, float(delay))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        #aruco parameters
        arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
        arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels

        #begin loop 
        ret, frame = cap.read()
        start = time.time()
        while ret==True and self.stopFlag.is_set()==False:
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
                                 "time" : time_video[frame_number]}
                    objects.append(detobject)
            
            
            if(len(objects)>0 and self.neighbourhood.parent != 0):
                msg = {"source" : self.neighbourhood.myself.__dict__,
                       "destination" : self.neighbourhood.parent.__dict__,
                       "method" : "detect",
                       "spec" : {"objects" : objects}}
                self.dicqueue.Qtosendunicast.put(msg)
            ####################################################
            if self.display:
                frameResized = cv2.resize(frame, (960,540))
                cv2.imshow(self.folder, frameResized)
                cv2.waitKey(1)

            
            if(frame_number>= time_video.size-1):
                #last frame
                break
            
            #wait time between two frames
            while time.time() <= time_video_now[frame_number+1]:
                cv2.waitKey(1)
            #capture new frame
            ret, frame = cap.read()
            frame_number+=1
            
        logging.debug("total time of detector offline = {} s".format(time.time()-start))
        cap.release()
        cv2.destroyWindow(self.folder)
    

