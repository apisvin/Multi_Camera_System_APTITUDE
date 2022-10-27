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
 
stopFlag = threading.Event() 

Qtosendunicast, Qtosendbroadcast, QtoHardwareManager = Queue(), Queue(), Queue()
hardware_manager = hardware_manager(QtoHardwareManager, Qtosendunicast, Qtosendbroadcast)

# Parameters of Benchmark
Master = True
BenchType = "bench1"
waitTitiemme = 30

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
        lt = launcher('tracking', 1, 'T', Qtosendunicast, Qtosendbroadcast, QtoHardwareManager)
        ld = launcher('detection', 0, "", Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)

        hardware_manager.add(lt)
        threading.Thread(target=lt.launch, args=()).start()
        hardware_manager.add(ld)
        threading.Thread(target=ld.launch, args=()).start()

        msg = {"source" : lt.n.myself.__dict__,
                "destination" : "all_agent",
                "method" : "benchmark",
                "spec" :BenchType}
        Qtosendbroadcast.put(msg)

    else:
        #create blank agent to wait for benchmark message from master 
        blank = launcher('blank', Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
        hardware_manager.add(blank)
        threading.Thread(target=blank.launch, args=()).start()
        #wait for message 
        msg = blank.dicqueue.Qtobenchmark.get()
        #remove blank agent from hardware
        msg = {"source" : "benchmarck",
                "destination" : "hardware_manager",
                "method" : "remove",
                "spec" : {"hardwareID" : blank.n.myself.hardwareID}}
        hardware_manager.QtoHardwareManager.put(msg)       
        #start creating agent 
        if(msg["spec"]=="bench1"):
            ld = launcher('detection', 1, Qtosendunicast = Qtosendunicast, Qtosendbroadcast = Qtosendbroadcast, QtoHardwareManager = QtoHardwareManager)
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