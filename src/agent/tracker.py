import uuid
import numpy as np
import time
from queue import Queue
import threading
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from collections import deque
import logging
import csv
from agent.agent import Agent

class Tracker(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        self.stopFlag = stopFlag
        self.display = True
        self.neighbourhood = neighbourhood 
        self.dicqueue = dicqueue
        self.dictracker = {} #dictionnary to manage all trackers
        self.Qtoplot = self.dicqueue.Qtoplot if self.display else 0
    
    def launch(self):
        #the role of this function is to distribute the observation to
        #the corresponding kalman filter. If there is none, it creates
        #a kalman filter
        df = 0
        if(self.display):
            threading.Thread(target=self.launch_plot, args=()).start()
        obj_counter = 0
        while self.stopFlag.is_set()==False:
            # take msh on the queue
            try:
                msg = self.dicqueue.Qtotracker.get(timeout=1)
                """
                bboxes = msg["spec"]["BBoxes2D"]["bboxes"]
                classIDs = msg["spec"]["BBoxes2D"]["class_IDs"]
                """
                objects = msg["spec"]["objects"]
                                    
                #for bbox, classID in zip(bboxes, classIDs):
                for detobject in objects:
                    # choose the corresponding tracker (kalman filter)
                    classID = detobject["objectID"]
                    position = detobject["position"]
                    px = position["x"]
                    py = position["y"]
                    key = self.get_kalman_key(classID)
                    if key ==-1:
                        # if no corresponding tracker -> launch new tracker
                        newTracker = kalman("aruco",classID)
                        self.dictracker["aruco_"+str(classID)] = newTracker
                        [x, y, ID] = newTracker.process_kalman([px, py])
                    else:
                        [x, y, ID] = self.dictracker["aruco_"+str(classID)].process_kalman([px, py])
                    
                    if self.display:
                        self.Qtoplot.put([x, y, ID])
                    
                    if self.neighbourhood.parent != 0:
                        msg = {"source" : self.neighbourhood.myself.__dict__,
                           "destination" : self.neighbourhood.parent.__dict__,
                           "method" : "track",
                           "spec" : {"x" : str(x),
                                     "y" : str(y),
                                     "id" : classID,
                                     "time" : time.time()}}
                        self.dicqueue.Qtosendunicast.put(msg)
            except:
                pass
        logging.debug("tracker stopped")
                        
    # return the tracker if the observation is close (<1m)
    def get_kalman_key(self, classID):
            #check if this identifier is in dictionnary of kalman
        if "aruco_"+str(classID) in self.dictracker:
            return "aruco_"+str(classID)
        else:
            return -1

    def launch_plot(self):
        list_marker = ['x', 'o', 'v', '^']
        plt.ion()
        fig, ax = plt.subplots()
        plt.axis([-250, 250, -250, 250])
        #ax = fig.add_subplot(111)
        marker = 0
        dicplot = {}
        while self.stopFlag.is_set()==False:
            #print("length Qtoplot = ", self.Qtoplot.qsize())
            xstate, ystate, kalman_id = self.Qtoplot.get()
            if(str(kalman_id) in dicplot): #line exists for kalman_id
                #print new data for this plot
                dicplot[str(kalman_id)].set_xdata(xstate)
                dicplot[str(kalman_id)].set_ydata(ystate)
            else:
                #create new plot and add to dicplot
                dicplot[str(kalman_id)], = ax.plot(xstate,ystate,list_marker[marker])#, label="object "+str(kalman_id))
                #ax.legend()
            fig.canvas.draw()
            #fig.canvas.flush_events()
               
def euclidean_distance(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)



class kalman():
    
    def __init__(self, classID, objectID):
        self.classID = classID
        self.objectID = objectID
        
        self.t = 0.0 #time to start Kalman
        
        self.dt = 0.0
    
        self.KF = KalmanFilter(dim_x=4, dim_z=2)

        self.KF.x = np.array([0., 0., 0., 0.])       # initial state (location, velocity)

        self.KF.F = np.array([[1.,0., self.dt, 0.],
                                [0.,1., 0., self.dt],
                                [0.,0., 1., 0.],
                                [0.,0., 0., 1.]])       # state transition matrix

        self.KF.H = np.array([[1.,0., 0., 0.],
                                [0.,1., 0., 0.]])       # Measurement function (only position)
        self.KF.P *= 30.                               # covariance matrix (already define as np.eye(dim_x))
        self.KF.R = np.array([[1.,0.],
                                [0., 1.]])               # state uncertainty
        #self.KF.Q = Q_discrete_white_noise(dim=4, dt=self.dt, var=0.1) # process uncertainty
        self.KF.Q = np.eye(4)*0.1
        self.state = self.KF.x
        
        self.statetoplot = deque([[0,0]]*10, maxlen=10)
             
    def process_kalman(self, position):
    
        # Prediction step
        self.KF.predict()
        camera = []
        reception_t = time.time()
        x = position[0]
        y = position[1]
        if(self.t == 0): #first observation
            self.KF.x = np.array([x, y, 0, 0]) # initial state (location, velocity and acceleration)
        if(self.t != 0):
            reception_t = time.time() 
            self.dt = reception_t - self.t
            self.KF.F = np.array([[1.,0., self.dt, 0.],
                        [0.,1., 0., self.dt],
                        [0.,0., 1., 0.],
                        [0.,0., 0., 1.]])          # update state transition matrix
            #G = np.array([0.5*self.dt**2, 0.5*self.dt**2, self.dt, self.dt]).T
            #self.KF.Q = G * G.T * 1
            self.KF.Q = np.eye(4)*self.dt
            obs = np.array([x, y])
            self.KF.update(obs)
        self.t = reception_t
        self.state = self.KF.x
        #send the 10 last state to plot
        #self.statetoplot.appendleft([self.state[0], self.state[1]])
        #xstate = [x[0] for x in self.statetoplot]
        #ystate = [x[1] for x in self.statetoplot]
        return [self.state[0], self.state[1], str(self.classID)+"_"+str(self.objectID)]
        #if self.Qtoplot != 0:
        #    self.Qtoplot.put([self.state[0], self.state[1], str(self.classID)+"_"+str(self.objectID)]) 
        """
        # send object msg to upper level
        if(self.neighbourhood.get_parent() != 0):
            #if I have a parent, i send my output as a detection
            detobject["position"] = {"x" : self.state[0],
                        "y" : self.state[1],
                        "z" : constants.ZPLAN}
            # dictionnary for msg to send
            msg = {"source" : "",
                   "destination" : "",
                   "method" : "detect",
                   "spec" : {"numbersObjects" : 1,
                             "objects" : [detobject]}}
            self.dicqueue["Qtoidentification"].put(msg)
        """
        
    
        
def write_state(filename, state):
    statestr = np.array2string(state, precision=4, separator=',')
    with open(filename, "a") as f:
        f.write(statestr[1:-1])
        f.write("\n")
        f.close()
        
def plot_file(filename):
    print("plot_file")
    with open(filename, "r") as f:
        for l in f:
            state = [float(d) for d in l.split(",")]
            plt.plot(state[0],state[1], 'ro')
        f.close()
    plt.show()
