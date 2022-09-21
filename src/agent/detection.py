import cv2
import numpy as np
from calib3d import Point3D, Point2D
import constants
import uuid
from matplotlib import pyplot as plt
import time
import sys

"""
create dictionnary :
{     
    "method" : "detect",
    "numberObjets" : int,
    "objects" :
    [
        detobject,
        detobject,
        ...
    ],
    "time" : time.time(),
    "messageID" : int
}
put dictionnary to queue to sender 
"""



class camera:
    """
    la classe camera utilise une camera Raspberry Pi afin de detecter des cibles aruco
    """
    def __init__(self, stopFlag, labo, calib, dicqueue, display=False):
        """
            labo : image to draw detected point
            calib : calibration object to transform 2D point to 3D point
            Qtosend : Queue to communicate with detection object
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.labo=labo
        self.calib = calib
        self.display = display
        
    def launch_camera(self):
        """
        boucle permettant la detection des codes aruco
        les position extraites sont traduites dans un repere commun (x,y) a chacune des cameras. 
        Une phase de calibration est necessaire
        """
        # Parameters
        LOWER_RED = constants.LOWER_RED
        UPPER_RED = constants.UPPER_RED
        
        LOWER_BLUE = constants.LOWER_BLUE
        UPPER_BLUE = constants.UPPER_BLUE
        
        COLORINFOS = constants.COLORINFOS
        WIDTH = constants.WIDTH
        HEIGHT = constants.HEIGHT
        
        #ArUco Marker constants
        
        # Sizing frames
        cap = cv2.VideoCapture(-1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, constants.FRAMEPERSECOND)
        
        #set buffersize to display without delay
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
           
        map_labo = np.array([0,0])
        
        cv2.namedWindow("frame", cv2.WINDOW_FULLSCREEN)
        #cv2.namedWindow("mask", cv2.WINDOW_FULLSCREEN)
        #cv2.namedWindow("labo", cv2.WINDOW_NORMAL)
        
        #time.sleep(3)
        # Loop for detection
        ret, frame = cap.read()
        time.sleep(0.001)
        ret, frame = cap.read()
        arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels
        while ret==True and self.stopFlag.is_set()==False:
            
            #capture image
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # Conversion RGB to HSV
            image = cv2.blur(image, (5, 5)) # Blur the image to expand the pixel 
            
            #ArUco marker def
            arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
            (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict,parameters=arucoParams)
                        
            #corners: A list containing the (x, y)-coordinates of our detected ArUco markers
            #ids : The ArUco IDs of the detected markers
            
            #mask for red colors
            mask_red = cv2.inRange(image, LOWER_RED, UPPER_RED) # Masquer tout ce qui est en dehors de la range
            mask_red = cv2.erode(mask_red, None, iterations = 4) # Erode the detected pixel to kill the artifacts. This is an algo use 4 time
            mask_red = cv2.dilate(mask_red, None, iterations = 4) # Dilate the number of pixel of the detected form. After the erosion, it is useful to have a big form.
            #mask for blue color
            mask_blue = cv2.inRange(image, LOWER_BLUE, UPPER_BLUE) # Masquer tout ce qui est en dehors de la range
            mask_blue = cv2.erode(mask_blue, None, iterations = 4) # Erode the detected pixel to kill the artifacts. This is an algo use 4 time
            mask_blue = cv2.dilate(mask_blue, None, iterations = 4) # Dilate the number of pixel of the detected form. After the erosion, it is useful to have a big form.
            
            #buffer to keep all objects 
            objects = []
            
            # Detection of red objects
            red_elements = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            #for multi object, parcourir la liste des objets detectes
            i = 0
            
            #ArUco detection
            if(ids is not None):
                ids = ids.flatten()
                for (markerCorner, markerID) in zip(corners, ids):
                    # extract the marker corners (which are always returned in
                    # top-left, top-right, bottom-right, and bottom-left order)
                    corners = markerCorner.reshape((4, 2))
                    #(topLeft, topRight, bottomRight, bottomLeft) = corners
                    i+=1
                    position = (int(corners[0][0]), int(corners[0][1]))
                    positionText = (int(corners[0][0]), int(corners[0][1])-15)
                    cv2.circle(frame, position, 12, (0, 0, 255), -1)
                    cv2.putText(frame, "Object_aruco_"+str(i), positionText, cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA)            
                    point3D = self.calib.project_2D_to_3D(Point2D(int(corners[0][0]), int(corners[0][1])), Z = constants.ZPLAN)

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
            
            '''
            # Colour detection
            for c in red_elements:
                area = cv2.contourArea(c)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(frame, "Object_red_" + str(i), (int(x) + 10, int(y) - 10), cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    i += 1
                    # Extract Point 3D (barycenter) from detected object
                    point3D = self.calib.project_2D_to_3D(Point2D(int(x+w/2), int(y+h/2)), Z = constants.ZPLAN)
                    cv2.circle(frame, (int(x+w/2), int(y+h/2)), 4, (0, 0, 255), -1)
                    # Matrix with position of detected object + translation of frame (repere) of dim_lab \ 2 (voir code calib) 
                    map_labo = np.vstack([map_labo, [int(point3D.x), int(point3D.y)]])
                    ####################################################
                    # dictionnary for detected object
                    objectID = i #uuid.uuid3(uuid.NAMESPACE_DNS, "RED").hex
                    classID = "RED"
                    position = {"x" : float(point3D.x),
                                "y" : float(point3D.y),
                                "z" : float(point3D.z)}
                    velocity = {"x'" : 0.0,
                                "y'" : 0.0,
                                "z'" : 0.0}
                    bbox = {"w" : w,
                            "h" : h,
                            "bboxFormat" : "rectangle",
                            "confInt" : 0.0}
                    detobject = {"objectID" : objectID,
                                 "classID" : classID,
                                 "position" : position,
                                 "velocity" : velocity,
                                 "bbox" : bbox}
                    objects.append(detobject)'''
            """
            # Detection of blue objects
            blue_elements = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            #for multi object, parcourir la liste des objets detectes
            i = 1
            for c in blue_elements:
                area = cv2.contourArea(c)
                if area > 500:
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), COLORINFOS, 2)
                    cv2.putText(frame, "Objet_blue_" + str(i), (int(x) + 10, int(y) - 10), cv2.FONT_HERSHEY_DUPLEX, 1, COLORINFOS, 1, cv2.LINE_AA)
                    
                    i += 1
                    # Extract Point 3D from detected object
                    point3D = self.calib.project_2D_to_3D(Point2D(int(x), int(y)), Z = constants.ZPLAN)
                    cv2.circle(self.labo, (int(x), int(y)), 4, (0,0,255), -1)
                    # Matrix with position of detected object + translation of frame (repere) of dim_lab \ 2 (voir code calib) 
                    map_labo = np.vstack([map_labo, [int(point3D.x), int(point3D.y)]])
                    ####################################################
                    # dictionnary for detected object
                    objectID = uuid.uuid3(uuid.NAMESPACE_DNS, "BLUE").hex
                    classID = "BLUE"
                    position = {"x" : float(point3D.x),
                                "y" : float(point3D.y),
                                "z" : float(point3D.z)}
                    velocity = {"x'" : 0.0,
                                "y'" : 0.0,
                                "z'" : 0.0}
                    bbox = {"w" : w,
                            "h" : h,
                            "bboxFormat" : "rectangle",
                            "confInt" : 0.0}
                    detobject = {"objectID" : objectID,
                                 "classID" : classID,
                                 "position" : position,
                                 "velocity" : velocity,
                                 "bbox" : bbox}
                    objects.append(detobject)"""
            
            if(len(objects)>0):
                # dictionnary for msg to send
                msg = {"source" : "",
                       "destination" : "",
                       "method" : "detect",
                       "spec" : {"numbersObjects" : len(objects),
                                 "objects" : objects}}
                #print("size of detect msg = ", sys.getsizeof(msg))
                self.dicqueue["Qtoidentification"].put(msg)
            ####################################################
                    
            if self.display:
                frameResized = cv2.resize(frame, (960,540))
                cv2.imshow("frame", frameResized)
                #laboResized = cv2.resize(self.labo, (960,540))
                #cv2.imshow("Labo", laboResized)
                #cv2.imshow('Image2', image2)
                #maskRedResized = cv2.resize(mask_red, (960,540))
                #cv2.imshow('mask', maskRedResized)
            
            cv2.waitKey(int((1/constants.FRAMEPERSECOND)*1000))
            ret, frame = cap.read()
                    
            # Break the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            

        cap.release()
        cv2.destroyAllWindows()
        
        #save output
        """
        plt.plot(map_labo[:,0], map_labo[:,1], '.')
        plt.savefig("/home/pi/TFE_TrackingObjects/local_data/output/map_labo.png")
        plt.xlim((-200,200))
        plt.ylim((-200,200))
        plt.savefig("/home/pi/TFE_TrackingObjects/local_data/output/map_labo_square.png")
        cv2.imwrite("/home/pi/TFE_TrackingObjects/local_data/output/labo_detected.png", self.labo)
        """

