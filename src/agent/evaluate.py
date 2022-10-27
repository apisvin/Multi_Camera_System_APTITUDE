import numpy
import logging
import csv
from sklearn.metrics import mean_squared_error
from scipy import interpolate
import matplotlib.pyplot as plt
import time

class evaluate():
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        self.stopFlag = stopFlag
        self.neighbourhood = neighbourhood 
        self.dicqueue = dicqueue

    def launch(self):
        gt_pos, gt_t, pred_pos, pred_t = [],[],[],[]
        with open("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/tracker.csv", "w", newline="") as dftracker:
            with open("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/vive.csv", "w", newline="") as dfvive:
                header = ["x", "y", "time"]
                wrt_tracker = csv.DictWriter(dftracker, fieldnames=header)
                wrt_tracker.writeheader()
                wrt_vive = csv.DictWriter(dfvive, fieldnames=header)
                wrt_vive.writeheader()
                while self.stopFlag.is_set()==False:
                    try:
                        msg = self.dicqueue.Qtoeval.get(timeout=1)
                        if msg["method"] == "track":
                            pred_pos.append([msg["spec"]["x"],msg["spec"]["y"]])
                            pred_t.append(msg["spec"]["time"])
                            #wrt_tracker.writerow({'x' : msg["spec"]["x"],
                            #                        'y' : msg["spec"]["y"],
                            #                        'time' : msg["spec"]["time"]})
                        elif msg["method"] == "GroundTruth":
                            gt_pos.append([float(msg["spec"]["x"]),float(msg["spec"]["y"])])
                            gt_t.append(time.time())
                    except:
                        pass
        logging.debug("gt_pos = {}".format(gt_pos))
        logging.debug("gt_t = {}".format(gt_t))
        compute_MSE(gt_pos, gt_t, pred_pos, pred_t, display = True)
        logging.debug("evaluate stopped")
        
def interpolate_data(position, time):
    """
    INPUT   : np array with data
    OUTPUT  : interpolation of data
    """       
    interpolate_position = interpolate.interp1d(time, position, axis=0, kind='cubic')
    return interpolate_position

def compute_MSE(gt_pos, gt_t, pred_pos, pred_t, display = False):
    """
    INPUT   : the two csv file with the results of the two tracks methods 
    OUTPUT  : the MSE score between the GT track & the predicted track
    """ 
    interpolation = interpolate_data(gt_pos, gt_t)
    
    truth_p_2_compute = []
    predicted_p_2_compute =[]
    number_sample = []
    MSEs = []

    for t, p in zip(pred_t, pred_pos):
        truth_p_2_compute.append(interpolation(t))
        predicted_p_2_compute.append(p)
        number_sample.append(len(truth_p_2_compute))

        MSE = mean_squared_error(truth_p_2_compute, predicted_p_2_compute)
        MSEs.append(MSE)

    if(display):
        plt.plot(number_sample, MSEs)
        plt.xlabel('Number of recorded data')
        plt.ylabel('MSE')
        plt.savefig("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/fig.png")
        plt.show()

    return MSEs