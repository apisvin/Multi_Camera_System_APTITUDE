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
from GUI.GUI_benchmark import *
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

def wait_as_slave():
    blank_l = launcher(agenttype="blank", level=0, DNS="blankdns", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = hardware_manager.QtoHardwareManager)
    hardware_manager.add(blank_l)
    threading.Thread(target=blank_l.launch, args=()).start()
    #wait for message
    logging.debug("waiting to begin benchmark")
    msg = blank_l.dicqueue.Qtobenchmark.get()
    while msg["method"]!="benchmark":
        msg = blank_l.dicqueue.Qtobenchmark.get()
    #remove blank agent from hardware
    msgremove = {"source" : "benchmarck",
            "destination" : "hardware_manager",
            "method" : "remove",
            "spec" : {"hardwareID" : blank_l.n.myself.hardwareID}}
    hardware_manager.QtoHardwareManager.put(msgremove)

def begin_master():
    blank_l = launcher(agenttype="blank", level=0, DNS="blankdns", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = hardware_manager.QtoHardwareManager)
    msg = {"source" : blank_l.n.myself.__dict__,
            "destination" : "all_agent",
            "method" : "benchmark",
            "spec" :""}
    Qtosendbroadcast.put(msg)

def main():
    launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    
    # launch a recorder agent as slave hardware
    slave = False
    testTime = 5*60 #[s]

    if slave:
        wait_as_slave()
    else:
        begin_master()
    
    #launch recorder
    l = launcher(agenttype=str.lower("recorder"), level=int(0), DNS="", Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast, QtoHardwareManager=hardware_manager.QtoHardwareManager)
    hardware_manager.add(l)
    threading.Thread(target=l.launch, args=()).start()
    #wait during testTime
    print("wait {} s".format(testTime))
    time.sleep(testTime)
    #stop
    msg = {"source" : "main",
        "destination" : "hardware_manager",
        "method" : "remove",
        "spec" : {"hardwareID" : l.n.myself.hardwareID}}
    hardware_manager.QtoHardwareManager.put(msg)


    

if __name__ == "__main__":
    main()