from queue import Queue
from collections import deque
import threading
import time
import sys
import select
from communication.inter.sender import *
from communication.inter.receiver import *
from communication.intra.watcher import *
from utils.neighbourhood import *
from utils.dicqueue import *
from agent.detector import *
from agent.offlineDetector import *
from agent.offlineDecentralized import *
from agent.decentralized import *
from agent.tracker import *
from agent.vive import *
from agent.recorder import *
from calibration.calibrate import *
import logging



class launcher:
    """
    la classe launcher cree les classes et 
    lance l ensemble des threads necessaires a la creation d un agent 
    On lui donne en argument toutes les infos de l agent cree et 
    c est lui qui cree dicqueue
    
    """

    def __init__(self, agenttype, Qtosendunicast, Qtosendbroadcast, QtoHardwareManager, folder=None, t_b=None):
        """
        Launcher class represents a agent and start all of its threads 
        This class contains all the informatioin relative to the agent.
        Args : 
            agenttype : string specifiing the type of agent
            Qtosendunicast : queue to send messages to sender_unicast
            Qtosendbroadcast : queue to send messages to sender_broadcast
            QtoHardwareManager : queue to send messages to the hardware_manager  
            folder : a folder assigned for the agent. It can either access or safe data in this folder dependeing of its type
            t_b : time from time.time() when the benchmark is launched
        """
        self.stopFlag = threading.Event() #Set() the flag stops all threads 
        self.dicqueue = dicqueue(Qtosendunicast, Qtosendbroadcast, QtoHardwareManager) #to store all Queue's (communication between threads)
        myself = neighbour(ip="", agenttype=agenttype) #to know all paramters of myself as neighbour
        myself.generate_own_IP()
        self.n = neighbourhood(myself) #to store all neighbours
        self.folder = folder
        self.t_b = t_b 
        
    def launch(self):
        """
        Procedure to start all threads running for a specific agent defined as a launcher class 
        First, identification task is launched. This task aims to understand messages from other agents
        and process them.
        Then, in function of the agent type, it launchs the specific task correspong to the agent.
        """
        self.launch_watcher()
        if(self.n.myself.agenttype == "blank"):
            pass
        elif(self.n.myself.agenttype == "recorder"):
            self.launch_recorder()
        elif(self.n.myself.agenttype == "vive"):
            self.launch_VIVE()
        elif(self.n.myself.agenttype == "offlinedecentralized"):
            self.launch_offlineDecentralized()
        elif(self.n.myself.agenttype == "decentralized"):
            self.launch_offlineDecentralized()
        

    
    def launch_watcher(self):
        """
        Procedure to start three threads of watcher
        """
        #add watcher to deal with missing agent
        w = watcher(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=w.receive_alive, args=()).start()
        threading.Thread(target=w.send_alive, args=()).start()
        threading.Thread(target=w.check_age, args=()).start()

    def launch_detection(self):
        """
        Procedure to start detection task. First, the camera has to be calibrated. From a image file 
        containing a picture of 9 aruco markers at specific coordinate, the Calib class is created.
        Then, the processing loop of the detector is launched.
        """
        #calibration
        image = cv2.imread('/home/pi/Multi_Camera_System_APTITUDE/local_data/image_calibration.png')
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
        
        d = Detector(self.stopFlag, self.n, self.dicqueue,calib, True)
        threading.Thread(target=d.launch, args=()).start()

    def launch_offlinedetection(self):
        """
        Procedure to start offlinedetection task. First, the camera has to be calibrated. From a image file 
        containing a picture of 9 aruco markers at specific coordinate, the Calib class is created.
        Then, the processing loop of the detector is launched.
        """
        d = OfflineDetector(self.stopFlag, self.n, self.dicqueue, self.folder, self.t_b)
        threading.Thread(target=d.launch, args=()).start()
        
        
    def launch_recorder(self):
        """
        Procedure to start the recording task. It create the Recorder and start the processing loop.
        """
        r = Recorder(self.stopFlag, self.dicqueue)
        threading.Thread(target=r.launch, args=()).start()
        
    def launch_VIVE(self):
        """
        Procedure to start the vive task. It create the Vive and start the processing loop.
        """
        v = Vive(self.stopFlag, self.dicqueue)
        threading.Thread(target=v.launch, args=()).start()

    def launch_offlineDecentralized(self):
        o = OfflineDecentralized(self.stopFlag, self.n, self.dicqueue, self.folder, self.t_b)
        threading.Thread(target=o.launch, args=()).start()

    def launch_decentralized(self):
        d = decentralized(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=d.launch, args=()).start()