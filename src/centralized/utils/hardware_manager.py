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
    
    def __init__(self, QtoHardwareManager, Qtosendunicast, Qtosendbroadcast, selforganization = False):
        """
        hardware_manager is a class that manage the creation and suppression of agents on the hardware.
        There is only one hardware_manager per hardware. Threads can communicate with this class to create
        or remove an agent.
        Args : 
            QtoHardwareManager : queue to send messages to this class 
            Qtosendunicast : queue to send messages to sender_unicast
            Qtosendbroadcast : queue to send messages to sender_broadcast
            selforganization : boolean to activate selforganization comportment
        """
        self.QtoHardwareManager = QtoHardwareManager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast
        self.selforganization = selforganization
        self.requestCreationRunning = False
        self.QtoReceiveRequestCreation = Queue()
        self.creationSupersivorRunning = False
        self.QtoReceiveCreationSupervisor = Queue()
        self.cpu = 0
        self.ram = 0
        self.launchers = {} #dictionnary containing all launcher classes indentified by their hardwareID

    #thread
    def hardware_manager(self):
        """
        Infinite loop running to manage agents on hardware.
        Two main operations are required : create and remove
        """
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
            if self.selforganization:
                if (msg["method"]=="parentDisappeared"):
                    self.parentDisappeared(msg)
                elif (msg["method"]=="childDisappeared"):
                    self.childDisappeared(msg)
                elif (msg["method"]=="request_creation"):
                    self.QtoReceiveRequestCreation.put(msg)
                elif (msg["method"]=="get_stat"):
                    self.get_stat(msg)
                elif (msg["method"]=="answer_stat"):
                    self.QtoReceiveCreationSupervisor.put(msg)


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
                if (self.cpu+self.ram)/2 > (received["spec"]["cpu"]+received["spec"]["ram"])/2:
                    create = False
                    logging.debug("receive_request_creation : my stats are not good to create")
                    break
            except:
                pass
        
        #this hardware_manager has to create the agent
        if create:
            l = launcher(agenttype=specdict["agenttype"], level=int(specdict["level"]), DNS=specdict["DNS"], Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.QtoHardwareManager)
            self.add(l)
            threading.Thread(target=l.launch, args=()).start()
            logging.debug("receive_request_creation : new agent created on this hardware : {}".format(l.n.myself.__dict__))
            #force the new agent to send a init message 
            msg = {"source" : l.n.myself.__dict__,
                "destination" : "broadcast",
                "method" : "init",
                "spec" : {"recreated" : "True"}}
            l.dicqueue.Qtosendbroadcast.put(msg)

        logging.debug("end of receive_request_creation")
        self.requestCreationRunning = False
            
            
    #thread
    def creation_supervisor(self, specdict):
        start = time.time()
        #clear queue from receiver
        #self.QtoReceiveRequestCreation.queue.clear()
        #compute own cost function
        cost = (self.ram+self.cpu)/2
        msg_creator_candidate = {"source" : "self",
                "destination" : "self",
                "method" : "create",
                "spec" : specdict}
        while time.time() - start < 10:
            try:
                received = self.QtoReceiveCreationSupervisor.get(timeout=1)
                if cost > (received["spec"]["cpu"]+received["spec"]["ram"])/2:
                    msg_creator_candidate["source"] = received["destination"]
                    msg_creator_candidate["destination"] = received["source"]
                    break
            except:
                pass
        
        #this hardware_manager has to create the agent
        if msg_creator_candidate["source"]=="self":
            #create blank agent with specified agenttype and level
            l = launcher(agenttype=specdict["agenttype"], level=int(specdict["level"]), DNS="", Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.QtoHardwareManager)
            self.add(l)
            threading.Thread(target=l.launch, args=()).start()
            logging.debug("new agent created on this hardware : {}".format(l.n.myself.__dict__))
        else:
            msg_creator_candidate["spec"]["DNS"]=""
            self.Qtosendunicast.put(msg_creator_candidate)

        logging.debug("end of creationSupersivor")
        self.creationSupersivorRunning = False
            


    def add(self,launcher):
        """
        add the launcher corresponding to the agent to the launchers list
        Args : 
            launcher : launcher class to add to the hardware
        """
        self.launchers[launcher.n.myself.hardwareID] = launcher

    def remove(self, hardwareID):
        """
        Remove the agent corresponding to the hardwareID from the launchers list
        Args : 
            hardwareID : hardwareID of the launcher to remove 
        """
        removed_launcher = self.get(hardwareID)
        removed_neighbourhood = removed_launcher.n          # extract neighbourhood of quitting agent
        logging.debug(removed_neighbourhood.myself.DNS + " is quitting")
        #send quit message to identification task
        msg = {"source" : removed_neighbourhood.myself.__dict__,
            "destination" : "",
            "method" : "quit",
            "spec" : {}}
        removed_launcher.dicqueue.Qtoidentification.put(msg)
        #set the flag to stop all threads associated to this agent 
        removed_launcher.stopFlag.set() 
        self.launchers.pop(hardwareID)
    
    def parentDisappeared(self, received):
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

    def childDisappeared(self, received):
        #create input for cost function:
        load1, load5, load15 = os.getloadavg()
        self.cpu = (load15/os.cpu_count()) * 100         # CPU usage (%)
        mem = psutil.virtual_memory()
        self.ram = mem.percent                               # RAM usage (%)

        #launch thread to receive 
        if self.creationSupersivorRunning == False:
            threading.Thread(target=self.creation_supervisor, args=(received["spec"]["disappeared"],)).start()
            self.creationSupersivorRunning = True
        #TODO
            
    
    def get_stat(self, received):
        #create input for cost function:
        load1, load5, load15 = os.getloadavg()
        self.cpu = (load15/os.cpu_count()) * 100         # CPU usage (%)
        mem = psutil.virtual_memory()
        self.ram = mem.percent                               # RAM usage (%)
        #create answer_stat
        msg = {"source" : received["destination"],
                "destination" : received["source"],
                "method" : "answer_stat",
                "spec" : {"cpu" : self.cpu,
                            "ram" : self.ram}}
        self.Qtosendunicast.put(msg)

    def get(self, hardwareID):
        """
        return the launcher class corresponding to the hardwareID
        """
        return self.launchers[hardwareID]
    
    def is_on_hardware(self, hardwareID):
        """
        return a boolean that tell if hardwareID is contained in launchers list
        """
        return hardwareID in self.launchers
    
    def get_dicqueue(self, hardwareID):
        """
        return the dicqueue class of the launcher corresponing to hardwareID
        """
        try:
            return self.launchers[hardwareID].dicqueue
        except:
            return -1
        
    def get_evaluate(self):
        """
        return a launcher class that correspond to a evaluator agent 
        """
        for l in self.launchers.values():
            if l.n.myself.agenttype=="evaluate":
                return l
        return -1
    
    def get_vive(self):
        """
        return a vive class that correspond to a vive agent 
        """
        for l in self.launchers.values():
            if l.n.myself.agenttype=="vive":
                return l
        return -1
        
    

