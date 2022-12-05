import logging
import numpy as np
import time
import csv
from agent.agent import Agent

class Vive(Agent):
    
    def __init__(self, stopFlag, dicqueue):
        """
        Vive records the position received from the VIVE tracker in the VR room
        Args : 
            stopFlag : flag to stop executing thread 
            dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag = stopFlag
        self.dicqueue = dicqueue
        
    def launch(self):
        with open("/home/pi/Multi_Camera_System_APTITUDE/results/VIVE.csv", "w", newline="") as df:
            header = ["x", "y", "time"]
            writer = csv.DictWriter(df, fieldnames=header)
            writer.writeheader()
            #purge queue
            while not self.dicqueue.QtoVIVE.empty():
                self.dicqueue.QtoVIVE.get(block=False)
            while self.stopFlag.is_set()==False:
                try:
                    msg = self.dicqueue.QtoVIVE.get(timeout=1)
                    writer.writerow({'x' : msg["spec"]["x"],
                                       'y' : msg["spec"]["y"],
                                        'time' : time.time()})
                except:
                    #the except catch the error from the get(timeout)
                    #This operation is necesssary to avoid the blocking property of the get() method
                    pass
            logging.debug("VIVE stopped")



