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
from GUI.GUI_benchmark import *

import logging
# level : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
 
stopFlag = threading.Event() 

Qtosendunicast, Qtosendbroadcast, QtoHardwareManager = Queue(), Queue(), Queue()
hardware_manager = hardware_manager(QtoHardwareManager, Qtosendunicast, Qtosendbroadcast)


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
    
    app = App(hardware_manager, Qtosendunicast, Qtosendbroadcast)
    app.mainloop()
        

if __name__ == "__main__":
    main()