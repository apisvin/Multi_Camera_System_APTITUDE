import numpy as np
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
        gt_pos, gt_t, gt_ids, pred_pos, pred_t, pred_ids = [],[],[],[],[],[]
        with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/tracker.csv", "w", newline="") as dftracker:
            with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/vive.csv", "w", newline="") as dfvive:
                header = ["x", "y", "time", "id"]
                wrt_tracker = csv.DictWriter(dftracker, fieldnames=header)
                wrt_tracker.writeheader()
                wrt_vive = csv.DictWriter(dfvive, fieldnames=header)
                wrt_vive.writeheader()
                while self.stopFlag.is_set()==False:
                    try:
                        msg = self.dicqueue.Qtoeval.get(timeout=1)
                        if msg["method"] == "track":
                            pred_pos.append([float(msg["spec"]["x"]),float(msg["spec"]["y"])])
                            pred_t.append(float(msg["spec"]["time"]))
                            pred_ids.append(int(msg["spec"]["id"]))
                            wrt_tracker.writerow({'x' : msg["spec"]["x"],
                                       'y' : msg["spec"]["y"],
                                        'time' : time.time()})
                        elif msg["method"] == "GroundTruth":
                            gt_pos.append([float(msg["spec"]["x"]),float(msg["spec"]["y"])])
                            gt_t.append(time.time())
                            gt_ids.append(0)
                            wrt_vive.writerow({'x' : msg["spec"]["x"],
                                       'y' : msg["spec"]["y"],
                                        'time' : time.time()})
                    except:
                        pass
                
            if len(gt_pos) != 0:
                MSEs = compute_MSE(gt_pos, gt_t, pred_pos, pred_t, display = True)
                MSE_at_position(pred_pos, pred_t, MSEs)
            else:
                logging.debug("No ground truth received")
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
        fig, ax = plt.subplots()
        ax.plot(number_sample, MSEs)
        ax.set_xlabel('Number of recorded data')
        ax.set_ylabel('MSE')
        plt.savefig("/home/pi/Multi_Camera_System_APTITUDE/local_data/MSE.png")
        #plt.show()

    return MSEs

def MSE_at_position(pred_pos, pred_t, MSEs):
    """
    INPUT   : positions evaluate by cameras & MSE score
    OUTPUT  : cmap of position with variation of MSE
    """
    list_marker = ['x', 'o', 'd', '^', 's', 'P', 'H']
    fig = plt.figure()
    plt.axis([-250, 250, -250, 250])

    #cm = plt.cm.get_cmap('jet')
    
    pred_pos = np.array(pred_pos)

    plt.scatter(x = pred_pos[:,0], y = pred_pos[:,1], c = MSEs, marker = 'x')#, cmap = cm)  
    
    plt.colorbar(label="MSE", orientation="vertical") 
    plt.savefig("/home/pi/Multi_Camera_System_APTITUDE/local_data/cmap_position_MSE.png")
