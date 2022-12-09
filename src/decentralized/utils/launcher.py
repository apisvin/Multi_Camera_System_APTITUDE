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
            self.launch_decentralized()
        elif(self.n.myself.agenttype == "car"):
            self.launch_car()
        

    def launch_watcher(self):
        """
        Procedure to start three threads of watcher
        """
        #add watcher to deal with missing agent
        w = watcher(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=w.receive_alive, args=()).start()
        threading.Thread(target=w.send_alive, args=()).start()
        threading.Thread(target=w.check_age, args=()).start()
        
    def launch_recorder(self):
        """
        Procedure to start the recording task. It create the Recorder and start the processing loop.
        """
        from agent.recorder import Recorder
        r = Recorder(self.stopFlag, self.dicqueue)
        threading.Thread(target=r.launch, args=()).start()
        
    def launch_VIVE(self):
        """
        Procedure to start the vive task. It create the Vive and start the processing loop.
        """
        from agent.vive import Vive
        v = Vive(self.stopFlag, self.dicqueue)
        threading.Thread(target=v.launch, args=()).start()

    def launch_offlineDecentralized(self):
        from agent.offlineDecentralized import OfflineDecentralized
        o = OfflineDecentralized(self.stopFlag, self.n, self.dicqueue, self.folder, self.t_b)
        threading.Thread(target=o.launch, args=()).start()

    def launch_decentralized(self):
        from agent.decentralized import decentralized
        d = decentralized(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=d.launch, args=()).start()

    def launch_car(self):
        from agent.car import car
        c = car(self.stopFlag, self.n, self.dicqueue)
        threading.Thread(target=c.launch, args=()).start()