import json
import mailbox
from queue import Queue
from utils.neighbourhood import *
from utils.neighbour import *
import time

class identification:
    """
    cette classe de permet de lancer la tache a la creation d un arbre dynamique compose des agents dans le reseau
    """
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        stopFlag : un flag permettant d arreter la tache en cours 
        neighbourhood : classe contenant l ensemble des agents dans le voisinage de l agent qui a lance identification
        dicqueue : dictionnaire de queue contenant l ensemble des queues qui permettent la communication entre taches 
        """
        self.stopFlag = stopFlag
        
        self.dicqueue = dicqueue #liste des queues
                
        self.neighbourhood = neighbourhood
        
    def loop_identification(self):
        """
        boucle permettant de traiter les differents messages recu relatifs aux connections entre agents
        """
        while(not self.neighbourhood.myself.DNS): #envoyer des init jusqu a reception du ackinit
            self.init() #envoyer un msg init
            if(not(self.dicqueue.Qtoidentification.empty())):
                received = self.dicqueue.Qtoidentification.get()
                if(received["method"]=="ackinit"):
                    self.received_ackinit(received)
                    
        self.dicqueue.Qtoidentification = Queue() #reset a new queue with bigger buffer
        while self.stopFlag.is_set()==False:
            received = self.dicqueue.Qtoidentification.get()
            #casing of msg
            if(received["method"]=="init" and len(self.neighbourhood.get_children())<2):
                print("init received")
                self.ackinit(received)
            elif(received["method"]=="ackparent"):
                self.received_ackparent(received)
            elif(received["method"]=="quit"):
                self.quit(received)
            elif(received["method"]=="ackquit"):
                self.ackquit(received)
            elif(received["method"]=="update"):
                self.ackupdate(received)
            elif(received["method"]=="look"):
                if(received["source"]["masterID"] == self.neighbourhood.myself.agentID):
                    # some agent is looking for me for being its master
                    self.acklook(received)
            elif(received["method"]=="acklook"):
                self.received_acklook(received)
            elif(received["method"]=="detect"):
                self.detect(received)
        print("identification stopped")
                    
    def init(self):
        """
        le message init s envoit a l'ensemble des agents du reseau
        il a pour but de trouver un master 
        le message contient toutes les infos de l agent qui envoit init 
        """
        msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : "broadcast",
                "method" : "init",
                "spec" : {}}
        self.dicqueue.Qtosendbroadcast.put(msg)
        time.sleep(2) #wait response
        
    def ackinit(self, receptedmsg):
        """
        ackinit est envoye apres la reception d un init recu d un agent qui appartient a un nivau inferieur 
        le message ackinit contient les infos de l agent qui envoit le message et les nouvelles infos de celui qui le recevra
        (sa nouvelle DNS, ID, ...)
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour(ip=dictagent["ip"], agenttype=dictagent["agenttype"], level=dictagent["level"], hardwareID=dictagent["hardwareID"])
        #for intern communication
        old_agentID = dictagent["agentID"]
        #condition for Xavier Claude and its cars
        #the new agent is a car and my agent is on top of the hierarchy
        if(newagent.agenttype == "car" and self.neighbourhood.parent == 0):
            numbneigh = len(self.neighbourhood.get_children())
            # Update information of child
            DNSagent  = newagent.agenttype + str(numbneigh) +"."+ self.neighbourhood.myself.DNS
            newagent.update_all_DNS(DNSagent, self.neighbourhood.myself.DNS)
            # give old agentID in the msg to identify task in intern communication
            newagent.agentID = old_agentID
            # Update list of child
            self.neighbourhood.update_children(newagent)
            # Creation of message to send back to child
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : newagent.__dict__,
                "method" : "ackinit",
                "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)
            print("New car : ", newagent.__dict__)
        #newagent is one level under and is not known
        elif(newagent.level + 1 == self.neighbourhood.myself.level):# and self.neighbourhood.IP_is_not_in_children(newagent)):
            # Check num of child
            numbneigh = len(self.neighbourhood.get_children())
            # Update information of child
            DNSagent  = newagent.agenttype + str(numbneigh) +"."+ self.neighbourhood.myself.DNS
            newagent.update_all_DNS(DNSagent, self.neighbourhood.myself.DNS)
            # Creation of message to send back to child
            msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : newagent.__dict__,
                "method" : "ackinit",
                "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)
        
    def received_ackinit(self, receptedmsg):
        """
        a la reception d un ackinit,
        cela met a jour les informations recu dans le message ackinit 
        envoit un ackparent au master afin qu il puisse mettre a jour sa liste d enfant 
        """
        #if i don t have a parent 
        if(self.neighbourhood.parent==0): 
            dictmyself = receptedmsg["destination"]
            self.neighbourhood.myself.update_all_DNS(dictmyself["DNS"], dictmyself["masterDNS"])
            dictparent = receptedmsg["source"]
            parent = neighbour(ip=dictparent["ip"], agenttype=dictparent["agenttype"], level=dictparent["level"], hardwareID=dictparent["hardwareID"])
            parent.update_DNS(dictparent["DNS"])
            self.neighbourhood.update_parent(parent)
            #send ack_parent
            msg = {"source" : self.neighbourhood.myself.__dict__,
                    "destination" : parent.__dict__,
                    "method" : "ackparent",
                    "spec" : {}}
            self.dicqueue.Qtosendunicast.put(msg)
        
    def received_ackparent(self, receptedmsg):
        """
        le message ackparent recu permet de mettre a jour la liste d 'enfant avec le nouvel enfant 
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour(ip=dictagent["ip"], agenttype=dictagent["agenttype"], level=dictagent["level"], hardwareID=dictagent["hardwareID"])
        newagent.DNS = dictagent["DNS"]
        newagent.agentID = dictagent["agentID"]
        newagent.masterDNS = dictagent["masterDNS"]
        newagent.masterID = dictagent["masterID"]
        # Update list of child
        self.neighbourhood.update_children(newagent)
        print(self.neighbourhood.myself.DNS + "'s new child is " + newagent.DNS)
                

    def quit(self, receptedmsg):
        """
        reception du message quit signifie que l agent source veut sortir du réseau
        etapes à gérer : 
           le message recu correspond a mon master :
               update mes infos perso
               prevenir les autres avec Look()
        if agent == mon parent -> update parent + chercher nouveau parent en envoyant look
        """
        if(self.neighbourhood.myself.agentID == receptedmsg["source"]["masterID"]):
            print("Child disappeared : ", receptedmsg["source"])
            self.neighbourhood.deleteChild(receptedmsg["source"]["agentID"])
        elif(self.neighbourhood.myself.masterID == receptedmsg["source"]["agentID"]):
            print("Parent disappeared : ", receptedmsg["source"])
            self.neighbourhood.myself.update_level_master()
            self.look()
        
    def look(self):
        """ 
        permet de chercher apres un nouveau parent
        la destination est "children" car la classe n a pas accès a l ensemble des enfants mais la classe sender a acces
        """
        msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : "children",
                "method" : "look",
                "spec" : {}
            }
        self.dicqueue.Qtosendbroadcast.put(msg)
        
    def acklook(self, receptedmsg):
        """
        de la meme maniere que ackinit mais pour la reception d un look
        les parametres de l 'agent source sont modifies afin qu il puisse se lier au nouveau parent 
        """
        dictagent = receptedmsg["source"]
        newagent = neighbour(ip=dictagent["ip"], agenttype=dictagent["agenttype"], level=dictagent["level"], hardwareID=dictagent["hardwareID"])

        DNSlist = dictagent["DNS"].split(".")
        separator = "."
        newDNS = separator.join([DNSlist[0], self.neighbourhood.myself.DNS])
        #update DNS
        newagent.update_all_DNS(newDNS, dictagent["masterDNS"])
        #add new agent to childhood
        self.neighbourhood.update_children_without_level(newagent)
        self.neighbourhood.printAllchildren()
        #send resp
        msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : newagent.__dict__,
                "method" : "acklook",
                "spec" : {"child" : newagent.__dict__}
            }
        self.dicqueue.Qtosendunicast.put(msg)
        
        
        
    def received_acklook(self, receptedmsg):
        """
        reception du acklook
        toutes les nouvelles infos sont dans "destination" pour l agent concerne et "source" pour le nouveau parent 
        """
        # update information from new parent
        self.neighbourhood.myself.update_DNS(receptedmsg["destination"]["DNS"])
        newParentdict = receptedmsg["source"]
        newParent = neighbour(ip=newParentdict["ip"], agenttype=newParentdict["agenttype"], level=newParentdict["level"], hardwareID=newParentdict["hardwareID"])
        newParent.update_all_DNS(newDNS=newParentdict["DNS"], newmasterDNS=newParentdict["masterDNS"])
        self.neighbourhood.update_parent_without_level(newParent)
        print("New parent of " +  self.neighbourhood.myself.DNS, " is " + self.neighbourhood.get_parent().DNS)
        #launch update to tell children that my DNS has changed
        self.update()
        
    #tell children that DNS has changed 
    def update(self):
        """
        permet de faire parcourir les nouvelles infos aux enfants
        """
        msg = {"source" : self.neighbourhood.myself.__dict__,
                "destination" : "children",
                "method" : "update",
                "spec" : {"children" : self.neighbourhood.get_children()}
        }
        self.dicqueue.Qtosendunicast.put(msg)
    
    #change new DNS of master
    def ackupdate(self, receptedmsg):
        """
        a la reception d un update :
        change les info selon l update (DNS) et itere l update si il y a des enfants 
        """
        newParentdict = receptedmsg["source"]
        self.neighbourhood.myself.update_master_DNS(newParentdict["DNS"])
        #my DNS
        DNSlist = self.neighbourhood.myself.DNS.split(".")
        separator = "."
        newDNS = separator.join([DNSlist[0], newParentdict["DNS"]])
        self.neighbourhood.myself.update_DNS(newDNS)
        #if children -> launch update
        if(len(self.neighbourhood.get_children())!=0):
            self.update()
            
    def detect(self, receptedmsg):
        receptedmsg["source"] = self.neighbourhood.myself.__dict__
        receptedmsg["destination"] = self.neighbourhood.get_parent().__dict__
        if receptedmsg["destination"] != 0:
            self.dicqueue.Qtosendunicast.put(receptedmsg)
        
        
    