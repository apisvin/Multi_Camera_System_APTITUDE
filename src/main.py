from queue import Queue
from collections import deque
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
    
    
    task1 = launcher(agenttype="blank", level=0, DNS="", Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast)
    neighbourhood_h.add(task1)
    threading.Thread(target=task1.launch, args=()).start()
    
    task2 = launcher(agenttype="blank", level=1, DNS="UA", Qtosendunicast=Qtosendunicast, Qtosendbroadcast=Qtosendbroadcast)
    neighbourhood_h.add(task2)
    threading.Thread(target=task2.launch, args=()).start()
    
    time.sleep(3)
    print("end main")

if __name__ == "__main__":
    main()