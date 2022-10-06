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
import psutil
import os
import time
    
class hardware_manager:
    
    def __init__(self, QtoHardwareManager, Qtosendunicast, Qtosendbroadcast):
        self.QtoHardwareManager = QtoHardwareManager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast
        self.requestCreationRunning = False
        self.QtoReceiveRequestCreation = Queue()
        self.cpu = 0
        self.ram = 0
        self.launchers = {} #contient l'esemble des launchers sur cette hardware identifiable par hardwareID

    #thread
    def hardware_manager(self):
        while True: 
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
            elif (msg["method"]=="disappear"):
                self.dispappear(msg)
            elif (msg["method"]=="request_creation"):
                self.QtoReceiveRequestCreation.put(msg)

    #thread
    def receive_request_creation(self, specdict):
        start = time.time()
        #clear queue from receiver
        #self.QtoReceiveRequestCreation.queue.clear()
        #compute own cost function
        cost = (self.ram+self.cpu)/2
        create = True
        while time.time() - start < 10:
            try:
                received = self.QtoReceiveRequestCreation.get(timeout=1)
                logging.debug("receive_request_creation : cpu = {} ram = {}".format(self.cpu, self.ram))
            except:
                pass
        
        #this hardware_manager has to create the agent
        if create:
            l = launcher(agenttype=specdict["agenttype"], level=int(specdict["level"]), DNS=specdict["DNS"], Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.QtoHardwareManager)
            self.add(l)
            threading.Thread(target=l.launch, args=()).start()
            logging.debug("new agent created on this hardware : {}".format(l.n.myself.__dict__))
            #force the new agent to send a init message 
            msg = {"source" : l.n.myself.__dict__,
                "destination" : "broadcast",
                "method" : "init",
                "spec" : {"recreated" : "True"}}
            l.dicqueue.Qtosendbroadcast.put(msg)

        logging.debug("end of receive_request_creation")
        self.requestCreationRunning = False
            


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
    
    def dispappear(self, received):
        #create input for cost function:
        load1, load5, load15 = os.getloadavg()
        self.cpu = (load15/os.cpu_count()) * 100         # CPU usage (%)
        mem = psutil.virtual_memory()
        self.ram = mem.percent                               # RAM usage (%)

        #launch thread to receive 
        if self.requestCreationRunning == False:
            threading.Thread(target=self.receive_request_creation, args=(received["spec"],)).start()
            self.requestCreationRunning = True

        #get all neighbours in cluster's source
        source_launcher = self.launchers[received["source"]["hardwareID"]]
        # send to each hardware_manager of the cluster
        for neighbour in source_launcher.n.get_hardware_manager_cluster():
            #generate request_creation message
            msg = {"source" : received["source"],
                "destination" : neighbour,
                "method" : "request_creation",
                "spec" : {"cpu" : self.cpu,
                            "ram" : self.ram}}
            logging.debug("requestion_creation sent to {}".format(neighbour))
            self.Qtosendunicast.put(msg)


    def get(self, hardwareID):
        return self.launchers[hardwareID]
    
    def is_on_hardware(self, hardwareID):
        return hardwareID in self.launchers
    
    def get_dicqueue(self, hardwareID):
        return self.launchers[hardwareID].dicqueue
    

