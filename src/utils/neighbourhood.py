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
        #self.myself = myself
        self.myself = myself
        
    def get_parent(self):
        return self.parent
    
    def get_children(self):
        return self.children
    
    #retourne l'index de l'element dans la liste. retourne -1 si pas dans la liste 
    def isInChildren(self, agent):
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
        #check all children
        self.lockChildren.acquire()
        for child in self.children:
            if(child.agentID == agentID):
                child.update_age()
        self.lockChildren.release()
        
        self.lockParent.acquire()
        if(self.parent != 0 and self.parent.agentID == agentID):
            self.parent.update_age()
        self.lockParent.release()
    
    #return boolean to tell if newagent IP is in children
    def IP_is_not_in_children(self, newagent):
        self.lockChildren.acquire()
        for n in self.children:
            if n.ip == newagent.ip:
                return False
            self.lockChildren.release()
        
        self.lockChildren.release()
        return True
    
    #update the parent list 
    def update_parent(self, newParent, browse=False):
        if (newParent.level == self.myself.level +1): #voisin deja dans la liste -> actualise age
            if browse:
                print("new agent added to list")
                self.printAll()
            self.lockParent.acquire()
            self.parent = newParent #add parent to neighbourhood
            self.lockParent.release()
    
    #if procedure look !!!
    def update_parent_without_level(self, newParent, browse=False):
        if browse:
            print("new parent added to list")
        self.lockParent.acquire()
        self.parent = newParent #add client to neighbourhood
        self.lockParent.release()
    
    #update the parent list 
    def update_children(self, newNeighbour, browse=False):
        index = self.isInChildren(newNeighbour)
        if (index == -1 and newNeighbour.level == self.myself.level - 1): 
            if browse:
                print("new agent added to list")
                self.printAll()
            self.lockChildren.acquire()
            self.children.append(newNeighbour) #add client to neighbourhood
            self.lockChildren.release()

    def update_children_without_level(self, newNeighbour, browse=False):
        index = self.isInChildren(newNeighbour)
        if (index == -1): #voisin deja dans la liste ?
            if browse:
                print("new agent added to list")
                self.printAll()
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
     
    def printAllchildren(self):
        print('Liste des enfants : ')
        i=1
        for n in self.children:
            print(n.__dict__)
            i=i+1
        print()
        
    def printParent(self):
        print("parent : ", self.parent)
        
        
    #Projet commun avec Xavier Claude
    #retourn the car agent 
    def get_car(self):
        for child in self.children:
            if(child.agenttype=="car"):
                return child.__dict__
        #print("no car in children")
        return -1
