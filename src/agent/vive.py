import logging
import numpy as np
import time
import csv

class vive():
    
    def __init__(self, stopFlag, dicqueue):
        self.stopFlag = stopFlag
        self.dicqueue = dicqueue
        
    def launch(self):
        with open("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/VIVE.csv", "w", newline="") as df:
            header = ["x", "y", "time"]
            writer = csv.DictWriter(df, fieldnames=header)
            writer.writeheader()
            while self.stopFlag.is_set()==False:
                try:
                    msg = self.dicqueue.QtoVIVE.get(timeout=1)
                    writer.writerow({'x' : str(msg[0]),
                                    'y' : str(msg[1]),
                                    'time' : time.time()})
                    logging.debug("msg in VIVE : {}".format(msg))
                except:
                    pass
            logging.debug("VIVE stopped")



