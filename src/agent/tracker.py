import uuid
import numpy as np
import time
from queue import Queue
import threading
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


class tracker():
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        self.stopFlag = stopFlag
        self.display_kalman = True
        self.neighbourhood = neighbourhood 
        self.dicqueue = dicqueue
        self.dictracker = {} #dictionnary to manage all trackers
        self.Qtoplot = Queue()
    
    def launch_tracker(self):
        #the role of this function is to distribute the observation to
        #the corresponding kalman filter. If there is none, it creates
        #a kalman filter
        #kalman_id = 0
        if(self.display_kalman):
            threading.Thread(target=self.launch_plot, args=()).start()

        obj_counter = 0
        while self.stopFlag.is_set()==False:
            # take msh on the queue
            msg = self.dicqueue["Qtotracker"].get()
            
            for detobject in msg["spec"]["objects"]:            
                # choose the corresponding tracker (kalman filter)
                key = self.get_kalman_key(detobject)
                if key ==-1:
                    # if no corresponding tracker -> launch new tracker
                    print("new tracker for ", detobject)
                    Qtokalman = Queue()
                    if detobject["classID"] == "aruco":
                        newTracker = kalman(self.stopFlag, self.neighbourhood, self.dicqueue, "aruco",detobject["objectID"], self.Qtoplot)
                        self.dictracker["aruco_"+str(detobject["objectID"])] = {"queue" : Qtokalman, "tracker" : newTracker}
                    else:
                        newTracker = kalman(self.stopFlag, self.neighbourhood, self.dicqueue, detobject["classID"], obj_counter, self.Qtoplot)
                        obj_counter+=1
                        self.dictracker[str(detobject["classID"])+"_"+str(detobject["objectID"])] = {"queue" : Qtokalman, "tracker" : newTracker}

                    threading.Thread(target=newTracker.launch_kalman, args=(Qtokalman,)).start()
                    Qtokalman.put(detobject)
                else:
                    Qtokalman = self.dictracker[key]["queue"]
                    Qtokalman.put(detobject)
    
    # return the tracker if the observation is close (<1m)
    def get_kalman_key(self, detobject):
        if detobject["classID"] == "aruco":
            #check if this identifier is in dictionnary of kalman
            if "aruco_"+str(detobject["objectID"]) in self.dictracker:
                return "aruco_"+str(detobject["objectID"])
            else:
                return -1
        else:   
            observation = np.array([detobject["position"]["x"], detobject["position"]["y"]])
            #check for color and position
            for key in self.dictracker:
                k = self.dictracker[key]["tracker"] #get kalman to extract position
                #same classID (same color)
                if k.classID == detobject["classID"]:
                    position = np.array([k.state[0], k.state[1]]) #extract position
                    #if the position of the kalman is near (1m) (and same color)
                    if(euclidean_distance(observation, position)<100):# and k.kalman_id == detobject["classID"]):
                       return key
        return -1

    def launch_plot(self):
        list_marker = ['x', 'o', 'v', '^']
        plt.ion()
        fig = plt.figure()
        plt.axis([-250, 250, -250, 250])
        ax = fig.add_subplot(111)
        marker = 0
        while self.stopFlag.is_set()==False:
            #print("length Qtoplot = ", self.Qtoplot.qsize())
            xstate, ystate, kalman_id = self.Qtoplot.get()
            if(str(kalman_id) in self.dicplot): #line exists for kalman_id
                #print new data for this plot
                self.dicplot[str(kalman_id)].set_xdata(xstate)
                self.dicplot[str(kalman_id)].set_ydata(ystate)
            else:
                #create new plot and add to dicplot
                self.dicplot[str(kalman_id)], = ax.plot(xstate,ystate,list_marker[marker], label="object "+str(kalman_id))
                ax.legend()
            fig.canvas.draw()
            fig.canvas.flush_events()
               
def euclidean_distance(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)



class kalman():
    
    def __init__(self, stopFlag, neighbourhood, dicqueue, classID, objectID, Qtoplot):
        self.stopFlag = stopFlag
        self.classID = classID
        self.objectID = objectID
        
        self.Qtoplot = Qtoplot
        
        self.t = 0.0 #time to start Kalman
        
        self.dt = 0.0
        
        self.neighbourhood = neighbourhood
        
        self.dicqueue = dicqueue
    
        self.KF = KalmanFilter(dim_x=6, dim_z=2)

        self.KF.x = np.array([0., 0., 0., 0., 0., 0.])       # initial state (location, velocity and acceleration)

        self.KF.F = np.array([[1.,0., self.dt, 0., self.dt**2, 0.],
                                [0.,1., 0., self.dt, 0, self.dt**2],
                                [0.,0., 1., 0., self.dt, 0.],
                                [0.,0., 0., 1., 0., self.dt],
                                [0.,0., 0., 0., 1., 0.],
                                [0.,0., 0., 0., 0., 1.]])       # state transition matrix

        self.KF.H = np.array([[1.,0., 0., 0., 0., 0.],
                                [0.,1., 0., 0., 0., 0.]])       # Measurement function (only position)
        self.KF.P *= 30.                               # covariance matrix (already define as np.eye(dim_x))
        self.KF.R = np.array([[1.,0.],
                                [0., 1.]])               # state uncertainty
        #self.KF.Q = Q_discrete_white_noise(dim=4, dt=self.dt, var=0.1) # process uncertainty
        self.KF.Q = np.eye(6)*0.1
        self.state = self.KF.x
        
        self.statetoplot = deque([[0,0]]*10, maxlen=10)
             
    def launch_kalman(self, queuefromtrackers):
        
        while self.stopFlag.is_set()==False:
            detobject = queuefromtrackers.get()
                
            # Prediction step
            self.KF.predict()
            camera = []
            reception_t = time.time()
            x = detobject["position"]["x"]
            y = detobject["position"]["y"]
            if(self.t == 0): #first observation
                self.KF.x = np.array([x, y, 0, 0, 0, 0]) # initial state (location, velocity and acceleration)
            if(self.t != 0):
                reception_t = time.time() 
                self.dt = reception_t - self.t
                self.KF.F = np.array([[1.,0., self.dt, 0., self.dt**2, 0.],
                            [0.,1., 0., self.dt, 0, self.dt**2],
                            [0.,0., 1., 0., self.dt, 0.],
                            [0.,0., 0., 1., 0., self.dt],
                            [0.,0., 0., 0., 1., 0.],
                            [0.,0., 0., 0., 0., 1.]])          # update state transition matrix
                #G = np.array([0.5*self.dt**2, 0.5*self.dt**2, self.dt, self.dt]).T
                #self.KF.Q = G * G.T * 1
                self.KF.Q = np.eye(6)*self.dt
                obs = np.array([x, y])
                self.KF.update(obs)
            self.t = reception_t
            self.state = self.KF.x
            #send the 10 last state to plot
            self.statetoplot.appendleft([self.state[0], self.state[1]])
            xstate = [x[0] for x in self.statetoplot]
            ystate = [x[1] for x in self.statetoplot]
            if self.Qtoplot != 0:
                self.Qtoplot.put([self.state[0], self.state[1], str(self.classID)+"_"+str(self.objectID)]) 
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
            
            #Projet commun avec Xavier Claude
            #Si il y a un agent "car" dans mon neighbourhood,
            #je lui envoie mon output
            dict_car = self.neighbourhood.get_car()
            if(dict_car!=-1):
                msg = {"source" : self.neighbourhood.myself.__dict__,
                       "destination" : dict_car,
                       "method" : "car",
                       "spec" : {"x" : self.state[0],
                            "y" : self.state[1],
                            "z" : constants.ZPLAN}}
                self.dicqueue["Qtosendunicast"].put(msg)
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
