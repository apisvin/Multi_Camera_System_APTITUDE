from queue import Queue
from collections import deque
import threading
import time
import sys
import select
from communication.inter.sender import *
from communication.inter.receiver import *
from communication.intra.identification import *
from utils.launcher import *
from utils.neighbourhood import *
import logging
    
class hardware_manager:
    
    def __init__(self, QtoHardwareManager, Qtosendunicast, Qtosendbroadcast):
        self.QtoHardwareManager = QtoHardwareManager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast
        self.launchers = {} #contient l'esemble des launchers sur cette hardware identifiable par hardwareID

    def launch(self):
        while True: #TODO mettre condition
            msg = self.QtoHardwareManager.get()
            if (msg["method"]=="create"):
                agenttype = msg["spec"]["agenttype"]
                level = msg["spec"]["level"]
                DNS = msg["spec"]["DNS"]
                l = launcher(agenttype=agenttype, level=int(level), DNS=DNS, Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.QtoHardwareManager)
                self.add(l)
                threading.Thread(target=l.launch, args=()).start()
            elif (msg["method"]=="remove"):
                self.remove(msg["spec"]["hardwareID"])

    def add(self,launcher):
        self.launchers[launcher.n.myself.hardwareID] = launcher

    def remove(self, hardwareID):
        #send quit message to identification task
        removed_launcher = self.get(hardwareID)
        removed_neighbourhood = removed_launcher.n          # extract neighbourhood of quitting agent
        logging.debug(removed_neighbourhood.myself.DNS + " is quitting")
        msg = {"source" : removed_neighbourhood.myself.__dict__,
            "destination" : "",
            "method" : "quit",
            "spec" : {}}

        removed_launcher.dicqueue.Qtoidentification.put(msg)
        
        time.sleep(3)
        removed_launcher.stopFlag.set() #set the flag to stop all threads associated to this agent 
        self.launchers.pop(hardwareID)

    def get(self, hardwareID):
        return self.launchers[hardwareID]
    
    def is_on_hardware(self, hardwareID):
        return hardwareID in self.launchers
    
    def get_dicqueue(self, hardwareID):
        return self.launchers[hardwareID].dicqueue
    

