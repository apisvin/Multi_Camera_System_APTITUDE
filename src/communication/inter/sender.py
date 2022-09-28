import socket
import json
from communication.inter.receiver import put_on_queue #TODO : mettre dans dicqueue
import logging

UDP_IP = ''


class sender:
    """
    la classe sender permet de traiter les messages sortant de l hardware.
    Pour des soucis d efficacite, une seule classe sender est creee par hardware.
    Cela permet de ne pas devoir ouvrir plusiers canaux de communication (socket).
    Afin de conaitre l ensemble des agents herberges sur l hardware, une variable manager_hardware est utilisee.
    Elle contient l ensemble des agents contenu sur l hardware. Il est possible de les distinguer par un identifier unique : hardware_ID
    """
    
    def __init__(self,manager_hardware, Qtosendunicast, Qtosendbroadcast):
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast
        self.manager_hardware = manager_hardware
        
        #self.neighbourhood = neighbourhood
        
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
        self.local_ip=IP
        
    
    def send_unicast(self):
        """
        envoie le message vers l agent de destination
        le message peut etre soit transmis directment vers un agent herberge sur le meme hardware ou
        il peut etre envoye a travers la socket vers l adresse ip de destination
        """
        PORT = 8000
        s_unicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            # Get message to send
            msg = self.Qtosendunicast.get()
            #check if the destination is on the same hardware
            if(self.manager_hardware.is_on_hardware(msg["destination"]["hardwareID"])):
                #put msg directly on his receiver queue
                dicqueue_dest = self.manager_hardware.get_dicqueue(msg["destination"]["hardwareID"])
                put_on_queue(msg, dicqueue_dest)
            #send msg on network
            else:                    
                if(msg["method"]=="update"):
                    children = msg["spec"]["children"]
                    msg["spec"].pop("children")
                    for child in children:
                        addr = (child.ip, PORT)
                        msg["destination"] = child.__dict__
                        msgJson = json.dumps(msg)
                        s_unicast.sendto(msgJson.encode(), addr)
 
                elif(msg["method"]=="detect"):
                    #return a list of agent tracking
                    if(msg["destination"] != 0): #if there is a tracker
                        addr = (msg["destination"]["ip"], PORT)
                        msgJson = json.dumps(msg)
                        s_unicast.sendto(msgJson.encode(), addr)
                    
                    
                else:
                    addr = (msg["destination"]["ip"], PORT)
                    msgJson = json.dumps(msg)
                    s_unicast.sendto(msgJson.encode(), addr)
                    
                
                    
    
    def send_broadcast(self):
        """
        envoie le message a tous les agents contenus sur le hardware et sur le reseau en broadcast
        """
        PORT = 8001
        s_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            # Get message to send
            msg = self.Qtosendbroadcast.get()
            #send to  all agents on same hardware
            for hardwareID, launcher in self.manager_hardware.launchers.items():
                if(hardwareID != msg["source"]["hardwareID"]): #Do not send to itself
                    put_on_queue(msg, launcher.dicqueue)
                
            #And send to network
            msgJson = json.dumps(msg)
            addr = ('192.168.0.255', PORT)
            s_broadcast.sendto(msgJson.encode(), addr)
               
    