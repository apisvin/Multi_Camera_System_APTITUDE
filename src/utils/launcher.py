import constants
from queue import Queue
from collections import deque
import threading
import time
import sys
import select
from communication.sender import *
from communication.receiver import *
from communication.identification import *
from communication.neighbourhood import *
from communication.watcher import *

from calibrateAruco.calibrate import *
from calibrateAruco.aruco import *
from detection.camera import *
from detection.detection import *
    

from kalman.kalman import *
from kalman.trackers import *

from test_performance.pingpong import *


class launcher:
    """
    la classe launcher cree les classes et 
    lance l ensemble des threads necessaires a la creation d un agent 
    
    """

    def __init__(self, agenttype, level, DNS, Qtosendunicast, Qtosendbroadcast, display_kalman=False, testtype = 0):
        self.stopFlag = threading.Event()
        self.AGENTTYPE = agenttype
        self.LEVEL = level
        self.DNS = DNS
        self.display_kalman = display_kalman
        self.dicqueue = {"Qtosendunicast" : Qtosendunicast,
            "Qtosendbroadcast" : Qtosendbroadcast,
            "Qfromrectokalman" : Queue(),
            "Qfromkalmantomain" : Queue(),
            "Qtowatcher" : Queue(),
            "Qtoidentification" : Queue(),#initialization to 1 to react quickly
            "Qtotestperformance" : Queue()} 
        myself = agent(ip="", agenttype=self.AGENTTYPE, level=self.LEVEL)
        myself.update_DNS(self.DNS)
        myself.generate_own_IP()
        self.n = neighbourhood(myself)
        self.testtype = testtype
        
    def launch(self):
        try:
            self.launch_identification()
            if(self.AGENTTYPE == "detection"):
                self.launch_detection()
            elif(self.AGENTTYPE == "tracking"):
                self.launch_trackers()
            elif(self.AGENTTYPE=="ping"):
                self.launch_ping()
            elif(self.AGENTTYPE=="pong"):
                self.launch_pong()
            while self.stopFlag.is_set()==False:
                time.sleep(10)
        except KeyboardInterrupt:
            self.run.set()
        print("task stopped")
        

    
    def launch_identification(self):
        i = identification(self.stopFlag, self.n, self.dicqueue, display=constants.DISPLAYNEIGHBOURHOOD)
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
        
    def launch_ping(self):
        p = pingpong(self.dicqueue, self.n, self.testtype)
        #send ping and receive pong
        threading.Thread(target=p.launch_send_ping, args=()).start()
        threading.Thread(target=p.launch_receive_pong, args=()).start()
        threading.Thread(target=p.save_graph, args=()).start()


    def launch_pong(self):
        p = pingpong(self.dicqueue, self.n, self.testtype)
        #send pong when receiving ping
        threading.Thread(target=p.launch_receive_ping, args=()).start()
        threading.Thread(target=p.save_graph, args=()).start()
def printLengthQueue(dicqueue):
    print("All length of dicqueue")
    print("Qtosendunicast : ", dicqueue["Qtosendunicast"].qsize())
    print("Qtosendbroadcast : ", dicqueue["Qtosendbroadcast"].qsize())
    print("Qfromrectokalman : ", dicqueue["Qfromrectokalman"].qsize())
    print("Qfromkalmantomain : ", dicqueue["Qfromkalmantomain"].qsize())
    print("Qtoidentification : ", dicqueue["Qtoidentification"].qsize())
    print("###################################")