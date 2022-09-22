from queue import Queue
from collections import deque
import threading
import time
import sys
import select
from communication.inter.sender import *
from communication.inter.receiver import *
from communication.intra.identification import *
from utils.neighbourhood import *
import logging
    
class neighbourhood_hardware:
    
    def __init__(self):
        self.tasks = [] #contient l'esemble des agents sur cette hardware
        #chaque task est identifiee par sa DNS
        
    def add(self,task):
        self.tasks.append(task)
        
    def delete(self,task):
        pass
    
    def is_on_hardware(self, hardwareID):
        for task in self.tasks:
            if(task.n.myself.hardwareID == hardwareID):
                return True
        return False
    
    def get_index(self, hardwareID):
        i=0
        for task in self.tasks:
            if(task.n.myself.hardwareID == hardwareID):
                return i
            i+=1
        return -1
    
    def get_dicqueue(self, hardwareID):
        index = self.get_index(hardwareID)
        if index == -1:
            return -1
        else:
            return self.tasks[index].dicqueue

    def remove(self, hardwareID):
        index = self.get_index(hardwareID)
        if index == -1:
            logging.ERROR("hardwareID not in tasks")
        else:
            self.tasks.pop(index)
    

