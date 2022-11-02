from queue import Queue
from collections import deque
import threading
import time
import sys
import select
from communication.inter.sender import *
from communication.inter.receiver import *
from communication.intra.identification import *
from communication.intra.watcher import *
from utils.neighbourhood import *
from utils.dicqueue import *
from agent.detector import *
from agent.tracker import *
from agent.evaluator import *
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

    def __init__(self, agenttype, level, DNS, Qtosendunicast, Qtosendbroadcast, QtoHardwareManager):
        self.stopFlag = threading.Event()                               #Flag to stop thread when agent is quitting 
        self.dicqueue = dicqueue(Qtosendunicast, Qtosendbroadcast, QtoHardwareManager)      #to store all Queue's (communication between threads)
        myself = neighbour(ip="", agenttype=agenttype, level=level)     #to know all paramters of myself as neighbour
        myself.update_DNS(DNS)
        myself.generate_own_IP()
        self.n = neighbourhood(myself)                                  #to store all neighbours
        
    def launch(self):
        self.launch_identification()
        if(self.n.myself.agenttype == "blank"):
            pass
        elif(self.n.myself.agenttype == "detector"):
            self.launch_detection()
        elif(self.n.myself.agenttype == "tracker"):
            self.launch_tracker()
        elif(self.n.myself.agenttype == "evaluator"):
            self.launch_evaluate()
        elif(self.n.myself.agenttype == "recorder"):
            self.launch_recorder()
        elif(self.n.myself.agenttype == "vive"):
            self.launch_VIVE()

    
    def launch_identification(self):
        i = identification(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=i.loop_identification, args=()).start()
        #add watcher to deal with missing agent
        w = watcher(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=w.receive_alive, args=()).start()
        threading.Thread(target=w.send_alive, args=()).start()
        threading.Thread(target=w.check_age, args=()).start()

    def launch_detection(self):
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
        
    def launch_tracker(self):
        t = Tracker(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=t.launch, args=()).start()
        
    def launch_evaluate(self):
        e = Evaluator(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=e.launch, args=()).start()
        
    def launch_recorder(self):
        r = Recorder(self.stopFlag, self.dicqueue)
        threading.Thread(target=r.launch, args=()).start()
        
    def launch_VIVE(self):
        v = Vive(self.stopFlag, self.dicqueue)
        threading.Thread(target=v.launch, args=()).start()