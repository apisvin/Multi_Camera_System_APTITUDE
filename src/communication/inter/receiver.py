import socket
import json
import logging

UDP_IP = ''


class receiver():
    
    def __init__(self, hardware_manager):
        """
        Class receiver is used to receive messages from other hardware. Sockets are used to communicate between hardware.
        Only one receiver is launched per hardware to avoid to open several channel

        Args : 
            hardware_manager : the hardware_manager of the hardware
            
        """
        self.hardware_manager = hardware_manager
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
        Listen the opened socket for broadcasted messages.
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
                for hardwareID, launcher in self.hardware_manager.launchers.items():
                    put_on_queue(dictReceived, launcher.dicqueue)
            

    def receive_unicast(self):
        """
        Listen the opened socket for unicasted messages. 
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
                #special case when msg is not from an agent but from GroundTruth
                if(dictReceived["source"]=="VIVE"):
                    #get tracker in hardware if there is one
                    launcher_evaluate = self.hardware_manager.get_evaluate()
                    if launcher_evaluate!=-1:
                        put_on_queue(dictReceived, launcher_evaluate.dicqueue)
                    launcher_vive = self.hardware_manager.get_vive()
                    if launcher_vive!=-1:
                        put_on_queue(dictReceived, launcher_vive.dicqueue)
                else:
                    #chercher la bonne dicqueue dans manager_hardware
                    dicqueue = self.hardware_manager.get_dicqueue(dictReceived["destination"]["hardwareID"])
                    if(dicqueue==-1):
                        logging.warning("message received (destination is not on hardware) : {}".format(dictReceived))
                    else:
                        put_on_queue(dictReceived, dicqueue)
                

def put_on_queue(dictReceived, dicqueue):
    """
    Process the message and put it on the correct queue of the dicqueue in function of the method field
    Args : 
        dictReceived : the received dictionnary to put on the right queue
        dicqueue : dicqueue class containing all queues
    """
    if(dictReceived["method"] == "init"):
        dicqueue.Qtoidentification.put(dictReceived)

    elif(dictReceived["method"] == "ackinit"):   
        dicqueue.Qtoidentification.put(dictReceived)
        
    elif(dictReceived["method"] == "ackparent"):    
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "quit"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "disappear"):
        dicqueue.Qtoidentification.put(dictReceived)
        
    if(dictReceived["method"] == "forward_disappear"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "look"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "acklook"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "update"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "initcluster"):
        dicqueue.Qtoidentification.put(dictReceived)

    if(dictReceived["method"] == "alive"):
        dicqueue.Qtowatcher.put(dictReceived)
        
    if(dictReceived["method"] == "detect"):
        dicqueue.Qtotracker.put(dictReceived)
        
    if(dictReceived["method"] == "track"):
        dicqueue.Qtoeval.put(dictReceived)

    if(dictReceived["method"] == "request_creation"):
        dicqueue.QtoHardwareManager.put(dictReceived)
        
    if(dictReceived["method"] == "get_stat"):
        dicqueue.QtoHardwareManager.put(dictReceived)
        
    if(dictReceived["method"] == "answer_stat"):
        dicqueue.QtoHardwareManager.put(dictReceived)
        
    if(dictReceived["method"] == "GroundTruth"):
        dicqueue.QtoVIVE.put(dictReceived)
        
    if(dictReceived["method"] == "benchmark"):
        dicqueue.Qtobenchmark.put(dictReceived)

