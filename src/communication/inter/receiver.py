import socket
import json
import logging

UDP_IP = ''


class receiver():
    """
    la classe receiver permet de traiter les messages entrant dans l hardware.
    Pour des soucis d efficacite, une seule classe receiver est creee par hardware.
    Cela permet de ne pas devoir ouvrir plusiers canaux de communication (socket).
    Afin de conaitre l ensemble des agents herberges sur l hardware, une variable neighbourhood_hardware est utilisee.
    Elle contient l ensemble des agents contenu sur l hardware. Il est possible de les distinguer par un identifier unique : hardware_ID
    """
    
    def __init__(self, neighbourhood_hardware):
        """
        ouvre le canal de connumication (socket)
        """
        self.neighbourhood_hardware = neighbourhood_hardware
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
        
    def receive_broadcast(self):
        """
        recoit les messages destines a tous les agents 
        """
        PORT = 8001
        #create socket in broadcast
        s_broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s_broadcast.bind((UDP_IP,PORT))
        #begin loop
        while True:
            msgReceived, address = s_broadcast.recvfrom(1024)
            msgReceived = msgReceived.decode()
            if(self.local_ip != address[0]): #message not from me 
                dictReceived = json.loads(msgReceived)
                for task in self.neighbourhood_hardware.tasks:
                    put_on_queue(dictReceived, task.dicqueue)
            

    def receive_unicast(self):
        """
        recoit les messages destines a l adresse ip du hardware
        traite le message recu afin de l envoyer vers l agent correspondant 
        """
        PORT = 8000
        #create socket in unicast
        s_unicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_unicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_unicast.bind((UDP_IP,PORT))
        while(True):
            msgReceived, address = s_unicast.recvfrom(8192)
            msgReceived = msgReceived.decode()
            if(self.local_ip != address[0]): #message not from me
                dictReceived = json.loads(msgReceived)
                #chercher la bonne dicqueue dans neighbourhood_hardware
                dicqueue = self.neighbourhood_hardware.get_dicqueue(dictReceived["destination"]["hardwareID"])
                if(dicqueue==-1):
                    logging.debug("message received (destination is not on hardware) : {}".format(dictReceived))
                else:
                    put_on_queue(dictReceived, dicqueue)
                

def put_on_queue(dictReceived, dicqueue):
    """
    traite le message recu : en fonction de la method du message, met le message recu sur la bonne queue 
    afin de l envoyer vers la bonne tache 
    """
    if(dictReceived["method"] == "init"):
        #dictReceived["agent"]["ip"]=address[0]
        dicqueue.Qtoidentification.put(dictReceived)

    elif(dictReceived["method"] == "ackinit"):   
        dicqueue.Qtoidentification.put(dictReceived)
        
    elif(dictReceived["method"] == "ackparent"):    
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "quit"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "disappear"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "look"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "acklook"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "update"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "alive"):
        dicqueue.Qtowatcher.put(dictReceived)
        
    if(dictReceived["method"] == "detect"):
        dicqueue.Qfromrectokalman.put(dictReceived)
        
    
