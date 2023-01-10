from queue import Queue
from collections import deque
from tkinter import *
from tkinter import ttk
import threading
import time
import sys
import select
from communication.inter.sender import *
from communication.inter.receiver import *
from communication.intra.identification import *
from communication.intra.watcher import *
from utils.dicqueue import *
from utils.launcher import *
from utils.neighbour import *
from utils.neighbourhood import *
from utils.hardware_manager import *
import logging

#configuration logging
logging.basicConfig(level=logging.DEBUG)
# DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.getLogger("matplotlib").setLevel(logging.WARNING)

Qtosendunicast, Qtosendbroadcast, QtoHardwareManager = Queue(), Queue(), Queue()
hardware_manager = hardware_manager(QtoHardwareManager, Qtosendunicast, Qtosendbroadcast)
    

def launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast):
    """
    Launch the four communication channels on the hardware : 
        receiver : 
            unicast : receive messages destinated to this ip address
            broadcast : receive messages destinated to all ip addresses
        sender : 
            unicast : send messages destinated to a specified ip address
            broadcast : send messages destinated to all ip addresses
    Args : 
        hardware_manager : the hardware_manager of the hardware
        Qtosendunicast (Queue) : Queue used to receive messages from other threads that want to communicate with specific IP address
        Qtosendbroadcast (Queue) : Queue used to receive messages from other threads that want to communicate all IP addesses
    """
    r = receiver(hardware_manager)    
    threading.Thread(target=r.receive_unicast, args=()).start()
    threading.Thread(target=r.receive_broadcast, args=()).start()
    
    s = sender(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    threading.Thread(target=s.send_unicast, args=()).start()
    threading.Thread(target=s.send_broadcast, args=()).start()

def launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast):
    """
    launch the hardware_manager
    Args : 
        hardware_manager : the hardware_manager of the hardware
        Qtosendunicast (Queue) : Queue used to receive messages from other threads that want to communicate with specific IP address
        Qtosendbroadcast (Queue) : Queue used to receive messages from other threads that want to communicate all IP addesses
    
    """
    threading.Thread(target=hardware_manager.hardware_manager, args=()).start()

def get_hardwareID(timeline, ID):
    for command in timeline:
        if command[0] == "ADD" and command[1] == ID:
            return command[6]
    return -1

def start_timeline(timeline):
    t_b = time.time() #delay in timeline
    for command in timeline:
        if command[0] == "ADD":
            DNS = command[2]
            agenttype = command[3]
            level = command[4]
            folder = command[5]
            l = launcher(agenttype=str.lower(agenttype), level=int(level), DNS=DNS, Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast, QtoHardwareManager=hardware_manager.QtoHardwareManager, folder=folder, t_b=t_b)
            #add hardwareID of launcher in lifetime
            command.append(l.n.myself.hardwareID)
            hardware_manager.add(l)
            threading.Thread(target=l.launch, args=()).start()
            logging.debug("ADD {}".format(agenttype))
        if command[0] == "REMOVE":
            # get hardwareID correspond with ID in lifetime
            ID = command[1]
            hardwareID = get_hardwareID(timeline, ID)
            msg = {"source" : "main",
                    "destination" : "hardware_manager",
                    "method" : "remove",
                    "spec" : {"hardwareID" : hardwareID}}
            hardware_manager.QtoHardwareManager.put(msg)
        if command[0] == "WAIT":
            t = command[1]
            logging.debug("wait {} sec".format(t))
            time.sleep(t)
            


def main():
    launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    
    """timeline represents the life of the process. It is organized as json with a list of different command :
    1. ["ADD", ID, DNS, agenttype, level, folder , hardwareID] : 
                - ID is a interger to identify the command 
                - DNS is the DNS of the new agent
                - agenttype is the agenttype of the new agent
                - level is the level of the new agent
                - folder is the folder containing the video file for offline processing
                - hardwareID is to be added once the agent is created in order to communicate with hardware_manager 
    2. ["REMOVE", ID]
                - ID given to the agent we want to remove 
    3. ["WAIT", time]
                - time in second to wait 
    """
    timeline = [["ADD", 0, "tracker", "tracker", 1, ""],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/SE"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/N"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/NW"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/S"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/SW"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/E"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/W"],
                ["ADD", 1, "", "offlineDetector", 0, "C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/centralized/videos/NE"],
                ["WAIT", 300],
                ["REMOVE", 0]]
    start_timeline(timeline)

    





if __name__ == "__main__":
    main()