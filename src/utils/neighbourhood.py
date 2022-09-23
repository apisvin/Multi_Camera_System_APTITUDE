import time
import json
from utils.neighbour import *
import threading

class neighbourhood:
    """
        la classe neighbourhood comprend une liste des neighbour de l'agent
    """
        
    def __init__(self, myself):
        self.lockParent = threading.Lock() #acquire and release to protect variable
        self.parent = 0
        
        self.lockChildren = threading.Lock() #acquire and release to protect variable
        self.children = []
        
        self.myself = myself

        self.lockCluster = threading.Lock() #acquire and release to protect variable
        self.cluster = []
        
    def get_parent(self):
        return self.parent
    
    def get_children(self):
        return self.children
    
    def isInChildren(self, agent):
        """retourne l'index de l'element dans la liste. retourne -1 si pas dans la liste """
        index = 0
        self.lockChildren.acquire()
        for n in self.children:
            if n.agentID == agent.agentID:
                self.lockChildren.release()
                return index
            index=index+1
        self.lockChildren.release()
        return -1
    
    def update_agent_age(self, agentID):
        """update age of agent with agentID"""
        self.lockChildren.acquire()
        for child in self.children:
            if(child.agentID == agentID):
                child.update_age()
        self.lockChildren.release()
        
        self.lockParent.acquire()
        if(self.parent != 0 and self.parent.agentID == agentID):
            self.parent.update_age()
        self.lockParent.release()

        for c in self.cluster:
            if(c.agentID == agentID):
                child.update_age()
    
    def IP_is_not_in_children(self, newagent):
        """return boolean to tell if newagent IP is in children"""
        self.lockChildren.acquire()
        for n in self.children:
            if n.ip == newagent.ip:
                return False
            self.lockChildren.release()
        
        self.lockChildren.release()
        return True
    
    def update_parent(self, newParent, browse=False):
        """update the parent with newparent"""
        if (newParent.level == self.myself.level +1): #voisin deja dans la liste -> actualise age
            self.lockParent.acquire()
            self.parent = newParent #add parent to neighbourhood
            self.lockParent.release()
    
    def update_parent_without_level(self, newParent, browse=False):
        """update the parent with newparent without checking level for look procedure"""
        self.lockParent.acquire()
        self.parent = newParent #add client to neighbourhood
        self.lockParent.release()
    
    #update the parent list 
    def update_children(self, newNeighbour, browse=False):
        """add newNeighbour in children list"""
        index = self.isInChildren(newNeighbour)
        if (index == -1 and newNeighbour.level == self.myself.level - 1): 
            if browse:
                print("new agent added to list")
                self.printAll()
            self.lockChildren.acquire()
            self.children.append(newNeighbour) #add client to neighbourhood
            self.lockChildren.release()

    def update_children_without_level(self, newNeighbour):
        """add newNeighbour in children list without checking level"""
        index = self.isInChildren(newNeighbour)
        if (index == -1): #voisin deja dans la liste ?
            self.lockChildren.acquire()
            self.children.append(newNeighbour) #add client to neighbourhood
            self.lockChildren.release()
    
    #delete from the list
    def deleteChild(self, deletedchildID):
        for child in self.children:
            if(deletedchildID == child.agentID):
                self.lockChildren.acquire()
                self.children.remove(child)
                self.lockChildren.release()

    def deleteCluster(self, deletedclusterID):
        for c in self.cluster:
            if(deletedclusterID == c.agentID):
                self.cluster.remove(c)
     
    def printAllchildren(self):
        print('Liste des enfants de ', self.myself.DNS)
        i=1
        for n in self.children:
            print(n.DNS)
            i=i+1
        print()
        
    def printParent(self):
        print("parent : ", self.parent)
        
    
    def add_to_cluster(self, newagent):
        self.cluster.append(newagent)

    def cluster_str(self):
        val = ""
        for c in self.cluster:
            val = val + "   " + c.DNS
        return val

    def get_all_neighbours(self):
        val = []
        if(self.parent != 0):
            val.append(self.parent)
        val.extend(self.children)
        val.extend(self.cluster)
        return val

    def get_children_asdict(self):
        val = []
        for child in self.children:
            val.append(child.__dict__)
        return val