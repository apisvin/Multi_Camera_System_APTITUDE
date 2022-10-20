import json
import mailbox
from queue import Queue
from utils.neighbourhood import *
from utils.neighbour import *
import time
import logging

class identification:
    """
    This class is associated to one agent. Its role is to discover and integrate other agent as neighbour 
    to the class neighbourhood. 
    """
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        stopFlag : a flag to stop the thread running loop_identication
        neighbourhood : a class containing all neighbours of the agent
        dicqueue : a class containing all queues to transmits messages between threads 
        """
        self.stopFlag = stopFlag        #set flag to kill all thread associated to an agent 
        
        self.dicqueue = dicqueue
                
        self.neighbourhood = neighbourhood
        
    def loop_identification(self):
        """
        loop to process the different messages received concerning the connections between agents
        """
        while(not self.neighbourhood.myself.DNS and self.stopFlag.is_set()==False): #envoyer des init jusqu a reception du ackinit
            self.init() 
            if(not(self.dicqueue.Qtoidentification.empty())):
                received = self.dicqueue.Qtoidentification.get()
                if(received["method"]=="ackinit"):
                    self.received_ackinit(received)
                    
        while self.stopFlag.is_set()==False:
            received = self.dicqueue.Qtoidentification.get()
            #casing of msg
            if(received["method"]=="init"):
                logging.debug("init received")
                self.ackinit(received)
            if(received["method"]=="ackinit"):
                    self.received_ackinit(received)
            elif(received["method"]=="ackparent"):
                self.received_ackparent(received)
            elif(received["method"]=="initcluster"):
                self.received_initcluster(received)
            elif(received["method"]=="quit"):
                self.quit(received)
                break #break the loop because the agent quit the network
            elif(received["method"]=="disappear"):
                self.disappear(received)
            elif(received["method"]=="forward_disappear"):
                self.forward_disappear(received)
            elif(received["method"]=="forward_disappear"):
                self.detect(received)
        logging.debug("identification stopped")
                    
    def init(self):
        """
        init messages are sent to all neighbours in the network (broadcast)
        the goal is to find a parent
        """
        msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : "broadcast",
                "method" : "init",
                "spec" : {}}
        self.dicqueue.Qtosendbroadcast.put(msg)
        time.sleep(2) #wait response
        
    def ackinit(self, receptedmsg):
        """
        ackinit messages are sent after reception of an init message
        to an agent that is directly under this one
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour.asdict(dictagent)
        logging.debug("init message is : {}".format(receptedmsg))
        #newagent is one level under and no DNS
        if(newagent.level + 1 == self.neighbourhood.myself.level
           and newagent.DNS == ""):
            DNSagent = self.neighbourhood.create_new_DNS(newagent)
            newagent.update_all_DNS(DNSagent, self.neighbourhood.myself.DNS)
            # create list of agent in the new agent's cluster (all children of myself)
            cluster = self.neighbourhood.get_children_asdict()
            # Creation of message to send back to child
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : newagent.__dict__,
                "method" : "ackinit",
                "spec" : {"cluster":cluster}}
            self.dicqueue.Qtosendunicast.put(msg)
        
        #new agent is one level under
        #and its DNS match mine as parent
        #and newagent is recreated
        if(newagent.level + 1 == self.neighbourhood.myself.level
           and self.neighbourhood.matchingDNSasParent(newagent.DNS)
           and "recreated" in receptedmsg["spec"]):
            logging.debug("init from ex child")
            #send ackinit to tell newagent that I am its parent
            # create list of agent in the new agent's cluster (all children of myself)
            cluster = self.neighbourhood.get_children_asdict()
            # Creation of message to send back to child
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : newagent.__dict__,
                "method" : "ackinit",
                "spec" : {"cluster":cluster}}
            self.dicqueue.Qtosendunicast.put(msg)
        
        #source agent is one level above,
        #parent is null and ["spec"]["recreate"] exists
        elif(newagent.level == self.neighbourhood.myself.level+1
                and self.neighbourhood.parent == 0 
                and "recreated" in receptedmsg["spec"]):
            #init from disappeared parent -> add parent and send ackparent
            newagent.update_DNS(receptedmsg["source"]["DNS"]) 
            self.neighbourhood.update_parent(newagent)
            self.neighbourhood.myself.update_master_DNS(receptedmsg["source"]["DNS"])
            logging.debug("disappeared parent {} retrieved for {}".format(self.neighbourhood.parent.DNS, self.neighbourhood.myself.DNS))
            msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : newagent.__dict__,
                    "method" : "ackparent",
                    "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)
            
        
    def received_ackinit(self, receptedmsg):
        """
        process received ackinit message : 
            parent neighbour is created and add to neighbourhood 
            cluster is extracted and initcluster is sent to all members of cluster
        """
        logging.debug("received ackinit for {}".format(self.neighbourhood.myself))
        #if i don t have a parent 
        if(self.neighbourhood.parent==0): 
            dictmyself = receptedmsg["destination"]
            #update myself DNS
            self.neighbourhood.myself.update_all_DNS(dictmyself["DNS"], dictmyself["masterDNS"])
            dictparent = receptedmsg["source"]
            #update parents DNS
            parent = neighbour(ip=dictparent["ip"], agenttype=dictparent["agenttype"], level=dictparent["level"], hardwareID=dictparent["hardwareID"])
            parent.update_DNS(dictparent["DNS"])
            self.neighbourhood.update_parent(parent)
            #send ack_parent
            msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : parent.__dict__,
                    "method" : "ackparent",
                    "spec" : {}}
            logging.debug("New agent created : {}".format(self.neighbourhood.myself.__dict__))
            self.dicqueue.Qtosendunicast.put(msg)
            #update cluster 
            for dictagent in receptedmsg["spec"]["cluster"]:
                self.neighbourhood.add_to_cluster(neighbour.asdict(dictagent))
            #send initcluster to each agent in cluster 
            for c in self.neighbourhood.cluster:
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : c.__dict__,
                    "method" : "initcluster",
                    "spec" : {}}
                self.dicqueue.Qtosendunicast.put(msg)
        
    def received_ackparent(self, receptedmsg):
        """
        ackparent is received to confirm that this agent become parent of source  
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour.asdict(dictagent)
        # Update list of child
        self.neighbourhood.update_children(newagent)

    def received_initcluster(self, receptedmsg):
        """
        a new agent in the cluster sent a initcluster to register in myself's cluster 
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour.asdict(dictagent)
        #add newagent to myself's cluster
        self.neighbourhood.add_to_cluster(newagent)
        logging.info("{}'s cluster is {}".format(self.neighbourhood.myself.DNS, self.neighbourhood.cluster_str()) )
                
    def quit(self, receptedmsg):
        """
        the reception of the quit message means that the agent wants to leave the network.
        The agent must then tell all its connections that it is disappearing (disappear message)
        Disappear messages are only sent horizontally  
        """
        children = self.neighbourhood.get_children()
        for c in children:
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : c.__dict__,
                "method" : "disappear",
                "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)
        parent = self.neighbourhood.get_parent()
        if parent!= 0:
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : parent.__dict__,
                "method" : "disappear",
                "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)


    def disappear(self, receptedmsg):
        """
        receiving the message disappear means that the source agent wants to leave the network
        """
        #my parent disappeared
        if(self.neighbourhood.parent != 0
                    and self.neighbourhood.parent.DNS == receptedmsg["source"]["DNS"]): #my parent disappeared
            logging.info("{}'s parent disappeared : {}".format(self.neighbourhood.myself.DNS, receptedmsg["source"])) 
            self.neighbourhood.myself.update_level_master()
            self.neighbourhood.parent = 0 #reset parent 
            #forward message to hardware manager to recreate parent 
            #spec are information about disappeared agent 
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : "hardware_manager",
                "method" : "parentDisappeared",
                "spec" : {"agenttype" : receptedmsg["source"]["agenttype"],
                            "level" : receptedmsg["source"]["level"],
                            "DNS" : receptedmsg["source"]["DNS"]}}
            self.dicqueue.QtoHardwareManager.put(msg)
        #my child disappeared && not a leader (its follower cannot recreate the agent 
        elif(self.neighbourhood.isChildrenFollower(receptedmsg["source"]["DNS"])):
            logging.debug("{} : follower child {} disappeared".format(self.neighbourhood.myself.DNS, receptedmsg["source"]["DNS"]))
            #delete from children
            self.neighbourhood.deleteChildwithDNS(receptedmsg["source"]["DNS"])
            #tell other children that this agent disappeared
            children = self.neighbourhood.get_children()
            for c in children:
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : c.__dict__,
                    "method" : "forward_disappear",
                    "spec" : {"disappeared" : receptedmsg["source"]}}
                self.dicqueue.Qtosendunicast.put(msg)
            #tell hardware_manager to recreate missing neighbour
            msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : "hardware_manager",
                    "method" : "childDisappeared",
                    "spec" : {"disappeared" : receptedmsg["source"]}}
            self.dicqueue.QtoHardwareManager.put(msg)
            #ask all hardware_manager of children to send their stat
            hardware_manager_children = self.neighbourhood.get_hardware_manager_children()
            for h in hardware_manager_children:
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : h,
                    "method" : "get_stat",
                    "spec" : {}}
                self.dicqueue.Qtosendunicast.put(msg)
            #procedure to recreate disappeared child
        #if source is in children && a leader
        elif(self.neighbourhood.isDNSinChildren(receptedmsg["source"]["DNS"])):
            #delete from children
            self.neighbourhood.deleteChildwithDNS(receptedmsg["source"]["DNS"])
            #tell other children that this agent disappeared
            children = self.neighbourhood.get_children()
            for c in children:
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : c.__dict__,
                    "method" : "forward_disappear",
                    "spec" : {"disappeared" : receptedmsg["source"]}}
                self.dicqueue.Qtosendunicast.put(msg)
            
        

    def forward_disappear(self, receptedmsg):
        """
        forward_disappear is sent by a parent to all its children when one of them leave
        """
        #source is in cluster
        if(self.neighbourhood.isDNSinCluster(receptedmsg["spec"]["disappeared"]["DNS"])):
            self.neighbourhood.deleteClusterwhitDNS(receptedmsg["spec"]["disappeared"]["DNS"])
            logging.debug("{} : neighbour {} in cluster disappeared".format(self.neighbourhood.myself.DNS, receptedmsg["spec"]["disappeared"]["DNS"]))


        
    def detect(self, receptedmsg):
        """
        send detection to parent
        """
        if self.neighbourhood.parent!=0:
            receptedmsg["destination"] = self.neighbourhood.parent.__dict__
            receptedmsg["source"] = self.neighbourhood.myself.__dict__
            self.dicqueue.Qtosendunicast.put(receptedmsg)