import time
import json
import uuid
import socket
import logging

class neighbour:
    
    def __init__(self, ip, agenttype, level, hardwareID=""):
        """
        The neighbor class represents an agent of the network. An agent is defined by :
            - its IP address : UDP socket identifier
            - its type : its predefined task that it must accomplish in the system (detection, tracking, ...)
            - its DNS : a string containing all the agents since the root. It is built recursively when an agent is inserted in the network
            - masterDNS : The DNS variable of the parent agent
            - level : the level in which the agent belongs in the tree. Level 0 is the lowest level agent (detection)
            - son age : the time since the last "alive" message was received
            - hardwareID : unique identifier given to the agent when it was created
        Args : 
            ip : IP address of the hardware containing the neighbour
            agenttype : type of the neighbour 
            level : level in which the neighbour is in the hierarchy
            hardwareID : unique uuid identifier for each neighbour 
        """
        self.ip=ip
        self.agenttype = agenttype
        self.DNS = ""
        self.masterDNS = ""
        self.level = level
        self.age = time.time()
        #if no specified hardwareID, create one
        if(hardwareID==""):
            self.hardwareID = uuid.uuid1().hex #random ID to identify neighbour on hardware 
        else:
            self.hardwareID = hardwareID #if specified, give hardwareID
        self.isLeader = False

    @classmethod
    def asdict(cls, dictagent):
        """
        constructor based on a dicionnary
        Args : 
            dictagent : dictionnary containing all the information required to create a neighbour
        """
        newNeighbour = cls(ip = dictagent["ip"], agenttype=dictagent["agenttype"], level=dictagent["level"])
        newNeighbour.DNS = dictagent["DNS"]
        newNeighbour.masterDNS = dictagent["masterDNS"]
        newNeighbour.age = time.time()
        newNeighbour.hardwareID = dictagent["hardwareID"]
        return newNeighbour
        
    
    def generate_own_IP(self):
        """
        Procedure that give the ip address of the hardware to the self.ip variable
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        self.ip=IP

    def update_IP(self, newIP):
        """
        Change ip address of the neighbour by newIP
        Args :
            newIP : new IP address to give to the neighbour
        """
        self.IP = newIP
    
    def update_DNS(self, newDNS):
        """
        Change DNS of the neighbour by newDNS
        Args :
            newDNS : new DNS to give to the neighbour
        """
        self.DNS = newDNS
    
    def update_master_DNS(self, newmasterDNS):
        """
        Change DNS's master of the neighbour by newmasterDNS
        Args :
            newmasterDNS : new DNS to give to the master
        """
        self.masterDNS = newmasterDNS
        
    def update_all_DNS(self, newDNS, newmasterDNS):
        """
        change the DNS of the neighbour and its master
        """
        self.update_DNS(newDNS)
        self.update_master_DNS(newmasterDNS)
    
    def update_level_master(self):
        """
        change the master of the neighbour for the master of the master 
        """
        DNSlist = self.masterDNS.split(".")
        separator = "."
        newmasterDNS = separator.join(DNSlist[1:])
        self.update_master_DNS(newmasterDNS)
        
    def update_age(self):
        """
        update the age of the neighbour
        """
        self.age = time.time()
    

