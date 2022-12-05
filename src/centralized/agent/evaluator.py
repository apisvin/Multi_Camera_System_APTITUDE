import numpy as np
import logging
import csv
from sklearn.metrics import mean_squared_error
from scipy import interpolate
import matplotlib.pyplot as plt
import time
from agent.agent import Agent

class Evaluator(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        Evaluator is the evaluating agent. It receives the fusioned measurements from Trackers and the 
        ground truth from VIVE tracker in the VR room.
        Args : 
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag = stopFlag
        self.neighbourhood = neighbourhood 
        self.dicqueue = dicqueue

    def launch(self):
        #create list to keep received data 
        gt_pos, gt_t, gt_ids, pred_pos, pred_t, pred_ids = [],[],[],[],[],[]
        #open file descriptor to write data in memory
        with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/tracker.csv", "w", newline="") as dftracker:
            with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/vive.csv", "w", newline="") as dfvive:
                #create the header for both files : tracker and VIVE
                header = ["x", "y", "time", "id"]
                wrt_tracker = csv.DictWriter(dftracker, fieldnames=header)
                wrt_tracker.writeheader()
                wrt_vive = csv.DictWriter(dfvive, fieldnames=header)
                wrt_vive.writeheader()
                #begin the loop
                while self.stopFlag.is_set()==False:
                    try:
                        msg = self.dicqueue.Qtoeval.get(timeout=1)
                        if msg["method"] == "track":
                            #append track position and time to lists
                            pred_pos.append([float(msg["spec"]["x"]),float(msg["spec"]["y"])])
                            pred_t.append(float(msg["spec"]["time"]))
                            pred_ids.append(int(msg["spec"]["id"]))
                            #write data in file 
                            wrt_tracker.writerow({'x' : msg["spec"]["x"],
                                       'y' : msg["spec"]["y"],
                                        'time' : time.time()})
                        elif msg["method"] == "GroundTruth":
                            #append ground truth position and time to lists
                            gt_pos.append([float(msg["spec"]["x"]),float(msg["spec"]["y"])])
                            gt_t.append(time.time())
                            gt_ids.append(0)
                            #write data in file 
                            wrt_vive.writerow({'x' : msg["spec"]["x"],
                                       'y' : msg["spec"]["y"],
                                        'time' : time.time()})
                    except:
                        #the except catch the error from the get(timeout)
                        #This operation is necesssary to avoid the blocking property of the get() method
                        pass
            #once loop finished, compute score as MSE  
            if len(gt_pos) != 0:
                MSEs = compute_MSE(gt_pos, gt_t, pred_pos, pred_t, display = True)
                MSE_at_position(pred_pos, MSEs)
            else:
                logging.debug("No ground truth received")
        logging.debug("evaluate stopped")
        
def interpolate_data(position, time):
    """
    function that return an interpolation of the position in function of time 
    Args : 
        position : np array with position
        time : np array with time
    """       
    interpolate_position = interpolate.interp1d(time, position, axis=0, kind='cubic')
    return interpolate_position

def compute_MSE(gt_pos, gt_t, pred_pos, pred_t, display = False):
    """
    function that return a list of the mean squared error (MSE) of each grounf truth time step
    Args : 
        gt_pos : position of ground truth
        gt_t : time of ground truth
        pred_pos : position of preditction
        pred_t : time of prediction
    """ 
    #as the reception of ground truth and tracking data is asynchronous,
    #an interpolation of the ground truth is needed to compare tracking position with ground truth 
    #at the same time
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

def MSE_at_position(pred_pos, MSEs):
    """
    Function that returns the occupancy map of the MSE in the experimental room at each ground truth 
    time step
    Args : 
        pred_pos : position in the VR room where the MSE is computed 
        MSEs : value of the MSE at each time step 
    """
    fig = plt.figure()
    plt.axis([-250, 250, -250, 250])
    #cm = plt.cm.get_cmap('jet')
    pred_pos = np.array(pred_pos)
    plt.scatter(x = pred_pos[:,0], y = pred_pos[:,1], c = MSEs, marker = 'x')#, cmap = cm)  
    plt.colorbar(label="MSE", orientation="vertical") 
    plt.savefig("/home/pi/Multi_Camera_System_APTITUDE/local_data/cmap_position_MSE.png")
