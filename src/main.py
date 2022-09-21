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

Qtosendunicast, Qtosendbroadcast = Queue(), Queue()
neighbourhood_h = neighbourhood_hardware()
    

def launch_hardware_com(neighbourhood_hardware, Qtosendunicast, Qtosendbroadcast):
    r = receiver(neighbourhood_hardware)
    s = sender(neighbourhood_hardware, Qtosendunicast, Qtosendbroadcast)
    
    t_receive_unicast = threading.Thread(target=r.receive_unicast, args=())
    #t_receive_unicast.deamon=True
    t_receive_unicast.start()
    
    threading.Thread(target=r.receive_broadcast, args=()).start()
    
    threading.Thread(target=s.send_unicast, args=()).start()
    threading.Thread(target=s.send_broadcast, args=()).start()


def main():
    launch_hardware_com(neighbourhood_h, Qtosendunicast, Qtosendbroadcast)
    
    app = App(neighbourhood_h, Qtosendunicast, Qtosendbroadcast)
    app.mainloop()
    

if __name__ == "__main__":
    main()