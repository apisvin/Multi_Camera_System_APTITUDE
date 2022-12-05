import json
from queue import Queue
from utils.neighbourhood import *
from utils.neighbour import *
import time
import logging

class watcher():
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        watcher is used to monitor the connection in neighbourhood. The class has three procedures running :
            send_alive : Send alive message to parent and children in neighbourhood to tell them that this agent is alive
            receive_alive : Receive alive messages from parent and children. It update the age variable of the source agent in neighbourhood
            check_age : check the age variable of parent and childrn in neighbourhood every $delay$ seconds. If the age exceeds 3*$delay$ seconds, the agent is supposed dead and removed from neighbourhood.

        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag = stopFlag            #set flag to kill all thread associated to an agent 
        self.neighbourhood=neighbourhood
        self.dicqueue = dicqueue
        self.delay = 5
        
        
    def receive_alive(self):
        """
        Receive alive messages from parent and children. It update the age variable of the source agent in neighbourhood
        """
        while self.stopFlag.is_set()==False:
            try:
                received = self.dicqueue.Qtowatcher.get(timeout=self.delay)
                #update age of neighbour
                self.neighbourhood.update_agent_age_leader(received["source"]["DNS"], received["spec"]["isLeader"])
                #update its status of leader
                
            except:
                pass
        logging.debug("receive_alive stopped")
            
    def send_alive(self):
        """
        Send alive message to parent and children in neighbourhood to tell them that this agent is alive 
        """
        while self.stopFlag.is_set()==False:
            for child in self.neighbourhood.get_children():
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : child.__dict__,
                    "method" : "alive",
                    "spec" : {"isLeader" : self.neighbourhood.is_leader()}}
                self.dicqueue.Qtosendunicast.put(msg)
            parent = self.neighbourhood.get_parent()
            if(parent != 0): #parent exists
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : parent.__dict__,
                    "method" : "alive",
                    "spec" : {"isLeader" : self.neighbourhood.is_leader()}}
                self.dicqueue.Qtosendunicast.put(msg)
            time.sleep(self.delay) #wait delay seconds
        logging.debug("send_alive stopped")
            
    def check_age(self):
        """
        check the age variable of parent and childrn in neighbourhood every $delay$ seconds. If the age exceeds 3*$delay$ seconds, the agent is supposed dead and removed from neighbourhood.
        """
        while self.stopFlag.is_set()==False:
            for child in self.neighbourhood.get_children():
                if(time.time() - child.age > 3*self.delay):
                    msg = {"source" : child.__dict__,
                        "destination" : self.neighbourhood.myself.__dict__,
                        "method" : "disappear",
                        "spec" : {}}
                    self.dicqueue.Qtoidentification.put(msg)
            parent = self.neighbourhood.get_parent()
            if(parent != 0 and time.time() - parent.age > 3*self.delay): #parent exists
                msg = {"source" : parent.__dict__,
                    "destination" : self.neighbourhood.myself.__dict__,
                    "method" : "disappear",
                    "spec" : {}}
                self.dicqueue.Qtoidentification.put(msg)
            time.sleep(3) #wait 5 seconds
        logging.debug("check_age stopped")