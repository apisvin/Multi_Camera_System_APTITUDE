import json
from queue import Queue
from communication.neighbourhood import *
from communication.agent import *
import time
import constants

class watcher():
    """
    la classe watcher permet surveiller l etat des connexions entre agents. 
    Elle envoie periodiquement des messages ALIVE a ses voisins en attendant une reponse de leur part.
    Si pas de reponse : la connexion est coupee 
    """
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        creation de classe watcher

        args:
            stopFlag : flag pour signaler la fin de la tache 
            neighbourhood : classe contenant l ensemble des voisins de l agent 
            dicqueue : dictionnaire de queue afin de comminiquer entre taches 
        """
        self.stopFlag = stopFlag
        self.neighbourhood=neighbourhood
        self.dicqueue = dicqueue
        self.delay = 5
        
        
    def receive_alive(self):
        """
        attend la reception des message ALIVE.
        Lorsqu un message est recu, il update l age du voisin correspond 
        """
        while self.stopFlag.is_set()==False:
            received = self.dicqueue["Qtowatcher"].get()
            #print("alive received from agentID = ", received["source"]["agentID"])
            self.neighbourhood.update_agent_age(received["source"]["agentID"])
        print("stopped")
            
    def send_alive(self):
        """
        envoie le message ALIVE a l ensemble de ses voisins
        """
        while self.stopFlag.is_set()==False:
            for child in self.neighbourhood.get_children():
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : child.__dict__,
                    "method" : "alive",
                    "spec" : {}}
                self.dicqueue["Qtosendunicast"].put(msg)
            parent = self.neighbourhood.get_parent()
            if(parent != 0): #parent exists
                msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : parent.__dict__,
                    "method" : "alive",
                    "spec" : {}}
                self.dicqueue["Qtosendunicast"].put(msg)
            time.sleep(self.delay) #wait delay seconds
        print("stopped")
            
    def check_age(self):
        """
        verifie pour chaque voisins son age. 
        Si son age est plus grand que le seuil (3 fois la duree entre message ALIVE)
        le voisin est concidere comme perdu. Un message quit dont la source est le voisin disparu 
        est envoye
        """
        while self.stopFlag.is_set()==False:
            for child in self.neighbourhood.get_children():
                if(time.time() - child.age > 3*self.delay):
                    #print("child passed away")
                    msg = {"source" : child.__dict__,
                        "destination" : self.neighbourhood.myself.__dict__,
                        "method" : "quit",
                        "spec" : {}}
                    self.dicqueue["Qtoidentification"].put(msg)
            parent = self.neighbourhood.get_parent()
            if(parent != 0 and time.time() - parent.age > 3*self.delay): #parent exists
                msg = {"source" : parent.__dict__,
                    "destination" : self.neighbourhood.myself.__dict__,
                    "method" : "quit",
                    "spec" : {}}
                self.dicqueue["Qtoidentification"].put(msg)
            time.sleep(3) #wait 5 seconds
        print("stopped")