import time
import json
import uuid
import socket
import logging

class neighbour:
    
    def __init__(self, ip, agenttype, level, hardwareID=""):
        """
        La classe neighbour représente un agent du reseau. Un agent est défini par :
            - son addresse IP : identifiant socket UDP
            - son type : sa tache prédéfini qu'il doit accomplir dans le système (detection, tracking, ...)
            - sa DNS : un string reprenant l ensemble des agent depuis la racine. Elle se construit de manière récursive lors de l'insertion d'un agent au réseau
            - agentID : identifiant unique assigne à un agent lors de son insertion
            - masterDNS : La variable DNS de l agent parent
            - masterID : l'agentID de son parent
            - level : le niveau dans lequel l agent appartient dans l arbre. Le niveau 0 est l agent de plus bas niveau (detection)
            - son age : le temps depuis la reception du dernier message "alive"
            - hadwareID : identifiant unique donne à l agent lors de sa creation
        """
        self.ip=ip
        self.agenttype = agenttype
        self.DNS = ""
        self.agentID = ""
        self.masterDNS = ""
        self.masterID = ""
        self.level = level #constants.LEVEL
        self.age = time.time()
        if(hardwareID==""):
            self.hardwareID = uuid.uuid1().hex #random ID to identify agent on hardware 
        else:
            self.hardwareID = hardwareID #if specified, give hardwareID

    @classmethod
    def asdict(cls, dictagent):
        newNeighbour = cls(ip = dictagent["ip"], agenttype=dictagent["agenttype"], level=dictagent["level"])
        newNeighbour.DNS = dictagent["DNS"]
        newNeighbour.agentID = dictagent["agentID"]
        newNeighbour.masterDNS = dictagent["masterDNS"]
        newNeighbour.masterID = dictagent["masterID"]
        newNeighbour.age = time.time()
        newNeighbour.hardwareID = dictagent["hardwareID"]
        return newNeighbour
        
    
    def generate_own_IP(self):
        """
        permet d extrait l adresse IP de l hardware
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
        change l'adresse IP par newIP
        """
        self.IP = newIP
    
    def update_DNS(self, newDNS):
        """
        change la DNS par newDNS et change la variable agentID
        """
        if(newDNS == ""):
            #no DNS
            self.agentID = 0
        else:
            self.DNS = newDNS
            self.agentID = uuid.uuid3(uuid.NAMESPACE_DNS, newDNS).hex
    
    def update_master_DNS(self, newmasterDNS):
        """
        change la DNS du master par newmasterDNS et change la variable masterID
        """
        self.masterDNS = newmasterDNS
        self.masterID = uuid.uuid3(uuid.NAMESPACE_DNS, newmasterDNS).hex
        
    def update_all_DNS(self, newDNS, newmasterDNS):
        """
        change la DNS de l agent et de son master
        """
        self.update_DNS(newDNS)
        self.update_master_DNS(newmasterDNS)
    
    def update_level_master(self):
        """
        change le master en pour son grand parent
        """
        DNSlist = self.masterDNS.split(".")
        separator = "."
        newmasterDNS = separator.join(DNSlist[1:])
        self.update_master_DNS(newmasterDNS)
        
    def update_age(self):
        """
        actualise la variable age
        """
        self.age = time.time()
    

