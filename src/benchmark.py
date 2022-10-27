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
# level : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
 
stopFlag = threading.Event() 

Qtosendunicast, Qtosendbroadcast, QtoHardwareManager = Queue(), Queue(), Queue()
hardware_manager = hardware_manager(QtoHardwareManager, Qtosendunicast, Qtosendbroadcast)

# Parameters of Benchmark
Master = False
BenchType = "bench1"
waitTime = 20

def launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast):
    r = receiver(hardware_manager)    
    threading.Thread(target=r.receive_unicast, args=()).start()
    threading.Thread(target=r.receive_broadcast, args=()).start()
    
    s = sender(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    threading.Thread(target=s.send_unicast, args=()).start()
    threading.Thread(target=s.send_broadcast, args=()).start()

def launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast):
    threading.Thread(target=hardware_manager.hardware_manager, args=()).start()

def main():
    launch_hardware_com(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    launch_hardware_manager(hardware_manager, Qtosendunicast, Qtosendbroadcast)

    if Master:
        le = launcher("evaluate", 2, "eval", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
        hardware_manager.add(le)
        threading.Thread(target=le.launch, args=()).start()

        msg = {"source" : le.n.myself.__dict__,
                "destination" : "all_agent",
                "method" : "benchmark",
                "spec" :BenchType}
        Qtosendbroadcast.put(msg)
        #wait
        time.sleep(waitTime)
        #remove evaluate 
        msgremove = {"source" : "benchmarck",
                "destination" : "hardware_manager",
                "method" : "remove",
                "spec" : {"hardwareID" : le.n.myself.hardwareID}}
        hardware_manager.QtoHardwareManager.put(msgremove)

    else:
<<<<<<< HEAD
        #create balnk agent to wait for benchmark message from master 
        blank = launcher("blank", 0, "blankdns", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
=======
        #create blank agent to wait for benchmark message from master 
        blank = launcher('blank', Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
>>>>>>> 63d5191d7efb9a75dc28520bc7b9d8b254ef6d8f
        hardware_manager.add(blank)
        threading.Thread(target=blank.launch, args=()).start()
        #wait for message
        logging.debug("waiting to begin benchmark")
        msg = blank.dicqueue.Qtobenchmark.get()
        while msg["method"]!="benchmark":
            msg = blank.dicqueue.Qtobenchmark.get()
        #remove blank agent from hardware
        msgremove = {"source" : "benchmarck",
                "destination" : "hardware_manager",
                "method" : "remove",
                "spec" : {"hardwareID" : blank.n.myself.hardwareID}}
<<<<<<< HEAD
        hardware_manager.QtoHardwareManager.put(msgremove)
=======
        hardware_manager.QtoHardwareManager.put(msg)       
>>>>>>> 63d5191d7efb9a75dc28520bc7b9d8b254ef6d8f
        #start creating agent 
        if(msg["spec"]=="bench1"):
            logging.debug("begin bench1")
            lt = launcher('tracking', 1, "", Qtosendunicast, Qtosendbroadcast, QtoHardwareManager)
            hardware_manager.add(lt)
            threading.Thread(target=lt.launch, args=()).start()
            
            ld = launcher('detection', 0, "", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
            hardware_manager.add(ld)
            threading.Thread(target=ld.launch, args=()).start()
        elif(msg["spec"]=="bench2"):
            ld = launcher('detection', 1, Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
            hardware_manager.add(ld)
            threading.Thread(target=ld.launch, args=()).start()
            time.sleep(waitTime)
            msg = {"source" : "benchmarck",
                    "destination" : "hardware_manager",
                    "method" : "remove",
                    "spec" : {"hardwareID" : ld.n.myself.hardwareID}}
            hardware_manager.QtoHardwareManager.put(msg)
        elif(msg["spec"]=="bench3"):
            time.sleep(waitTime)
            l = launcher(agenttype=agenttype, level=level, DNS=DNS, Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast, QtoHardwareManager=hardware_manager.QtoHardwareManager)
            hardware_manager.add(l)
            threading.Thread(target=l.launch, args=()).start()
    while True:
        time.sleep(10)
        

if __name__ == "__main__":
    main()