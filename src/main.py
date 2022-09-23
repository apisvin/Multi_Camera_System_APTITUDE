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
from utils.neighbourhood_hardware import *
from GUI.GUI import *

import logging
# level : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG)

Qtosendunicast, Qtosendbroadcast = Queue(), Queue()
neighbourhood_h = neighbourhood_hardware()
    

def launch_hardware_com(neighbourhood_hardware, Qtosendunicast, Qtosendbroadcast):
    r = receiver(neighbourhood_hardware)    
    threading.Thread(target=r.receive_unicast, args=()).start()
    threading.Thread(target=r.receive_broadcast, args=()).start()
    
    s = sender(neighbourhood_hardware, Qtosendunicast, Qtosendbroadcast)
    threading.Thread(target=s.send_unicast, args=()).start()
    threading.Thread(target=s.send_broadcast, args=()).start()


def main():
    launch_hardware_com(neighbourhood_h, Qtosendunicast, Qtosendbroadcast)
    
    app = App(neighbourhood_h, Qtosendunicast, Qtosendbroadcast)
    app.mainloop()
    

if __name__ == "__main__":
    main()