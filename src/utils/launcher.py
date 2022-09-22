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
import logging



class launcher:
    """
    la classe launcher cree les classes et 
    lance l ensemble des threads necessaires a la creation d un agent 
    On lui donne en argument toutes les infos de l agent cree et 
    c est lui qui cree dicqueue
    
    """

    def __init__(self, agenttype, level, DNS, Qtosendunicast, Qtosendbroadcast):
        self.stopFlag = threading.Event()                               #Flag to stop thread when agent is quitting 
        self.dicqueue = dicqueue(Qtosendunicast, Qtosendbroadcast)      #to store all Queue's (communication between threads)
        myself = neighbour(ip="", agenttype=agenttype, level=level)     #to know all paramters of myself as neighbour
        myself.update_DNS(DNS)
        myself.generate_own_IP()
        self.n = neighbourhood(myself)                                  #to store all neighbours
        
    def launch(self):
        self.launch_identification()
        if(self.n.myself.agenttype == "blank"):
            pass
        elif(self.n.myself.agenttype == "detection"):
            self.launch_detection()
        elif(self.n.myself.agenttype == "tracking"):
            self.launch_trackers()
        

    
    def launch_identification(self):
        i = identification(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=i.loop_identification, args=()).start()
        #add watcher to deal with missing agent
        w = watcher(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=w.receive_alive, args=()).start()
        threading.Thread(target=w.send_alive, args=()).start()
        threading.Thread(target=w.check_age, args=()).start()

    def launch_detection(self):
        #ATTENTION : pas oublier de recréer le fichier pickle avant tout
        create_pickle()
        calib = Calib.load("/home/pi/TFE_TrackingObjects/local_data/pickle/calib.pickle")
        labo=cv2.imread("/home/pi/TFE_TrackingObjects/local_data/images_labo/image_repere.png")
        c = camera(self.stopFlag, labo, calib, self.dicqueue, True)
        threading.Thread(target=c.launch_camera, args=()).start()
        
    def launch_trackers(self):
        t = trackers(self.stopFlag, self.n, self.dicqueue, self.display_kalman)
        #k = kalman(self.n, self.dicqueue)
        threading.Thread(target=t.launch_trackers, args=()).start()
        
