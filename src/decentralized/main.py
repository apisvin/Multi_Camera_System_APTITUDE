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
from communication.intra.watcher import *
from utils.dicqueue import *
from utils.launcher import *
from utils.neighbour import *
from utils.neighbourhood import *
from utils.hardware_manager import *
from GUI.GUI import *
import logging

#configuration logging
logging.basicConfig(level=logging.DEBUG)
# DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("aptitude-toolbox").setLevel(logging.WARNING)

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


def main():
    launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    
    #in decenttralized architecture, each camera performs detection and tracking 
    l = launcher(agenttype="decentralized", Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast, QtoHardwareManager=hardware_manager.QtoHardwareManager)
    hardware_manager.add(l)
    threading.Thread(target=l.launch, args=()).start()
    

if __name__ == "__main__":
    main()