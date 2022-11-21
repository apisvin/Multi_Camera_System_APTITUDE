import numpy as np
import time
from queue import Queue
import threading
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from collections import deque
import logging
import csv
from agent.agent import Agent

class Tracker(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue, display = False, save=True):
        """
        Tracker is the traking agent. It receives the detection in 3D coordinate in the global frame and 
        fusions all the detection. The fusion is implemented as a Kalman filter.
        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
            display : boolean for displaying in a window the occupancy map of targets
            save : boolean for saving data
        """
        self.stopFlag = stopFlag
        self.display = display
        self.save = save
        self.neighbourhood = neighbourhood 
        self.dicqueue = dicqueue
        self.dictracker = {} #dictionnary to manage all targets
        self.Qtoplot = self.dicqueue.Qtoplot if self.display else 0
    
    def launch(self):
        """
        Launch the tracking loop. It receives the coordinates of targets from its children.
        From the id of the aruco marker, it identifies the target. 
        Then, its give the measurements to the Kalman filter.
        If the display boolean variable is True, a new thread is created to plot is real time the 
        occupancy map. The communication with this thread is provided by Qtoplot Queue variable.
        """
        #create thread if display variable 
        if(self.display):
            threading.Thread(target=self.launch_plot, args=()).start()

        if self.save:
            x_save = []
            y_save = []
            time_save = []
        #begin the loop
        while self.stopFlag.is_set()==False:
            try:
                # take msg on the queue.
                # timeout is setted to stop the thread even if the get function is blocking
                msg = self.dicqueue.Qtotracker.get(timeout=1)
                """
                bboxes = msg["spec"]["BBoxes2D"]["bboxes"]
                classIDs = msg["spec"]["BBoxes2D"]["class_IDs"]
                """
                objects = msg["spec"]["objects"]
                                    
                #for bbox, classID in zip(bboxes, classIDs):
                for detobject in objects:
                    # extract variable from msg
                    classID = detobject["objectID"]
                    position = detobject["position"]
                    px = position["x"]
                    py = position["y"]
                    time = detobject["time"]
                    
                    if str(classID) in self.dictracker:
                        #if the received target is know, process the observation in kalman filter
                        [x, y, ID] = self.dictracker[str(classID)].process_kalman([px, py])
                    else:
                        #if the received target is not know, create a new kalman filter and process the observation
                        newTracker = kalman("aruco",classID)
                        self.dictracker[str(classID)] = newTracker
                        [x, y, ID] = newTracker.process_kalman([px, py])
                    
                    if self.display:
                        #send the new estimate of the position to plot 
                        self.Qtoplot.put([x, y, ID])

                    if self.save:
                        x_save.append(x)
                        y_save.append(y)
                        time_save.append(time)
                    
                    if self.neighbourhood.parent != 0:
                        #if a parent is known, send the estimate
                        msg = {"source" : self.neighbourhood.myself.__dict__,
                           "destination" : self.neighbourhood.parent.__dict__,
                           "method" : "track",
                           "spec" : {"x" : str(x),
                                     "y" : str(y),
                                     "id" : classID,
                                     "time" : time.time()}}
                        self.dicqueue.Qtosendunicast.put(msg)
            except:
                #the except catch the error from the get(timeout)
                #This operation is necesssary to avoid the blocking property of the get() method
                pass
        if self.save:
            header = ["x", "y", "time"]       
            with open("C:/Users/Aurora/Multi_Camera_System_APTITUDE/local_data/tracks.csv", "w") as df:
                #write all detections in a single csv file
                trackWriter = csv.DictWriter(df, fieldnames=header)
                trackWriter.writeheader()
                for i in range(len(x_save)):
                    trackWriter.writerow({"x": x_save[i],
                                            "y": y_save[i],
                                            "time" : time_save[i]})
        logging.debug("tracker stopped")
        

    def launch_plot(self):
        """
        Method to display the occupancy map of the tragets.
        """
        plt.ion() #enalble interactive plotting for real time process
        fig, ax = plt.subplots()
        plt.axis([-250, 250, -250, 250]) #fix the size of the map with the size of the room (5x5m)
        dicplot = {} #dictionnary to keep the coordinate of each target

        while self.stopFlag.is_set()==False:
            xstate, ystate, kalman_id = self.Qtoplot.get()
            if(str(kalman_id) in dicplot):
                #set the new coordinate of the traget
                dicplot[str(kalman_id)].set_xdata(xstate)
                dicplot[str(kalman_id)].set_ydata(ystate)
            else:
                #create new target and add to dicplot
                dicplot[str(kalman_id)], = ax.plot(xstate,ystate,'x')#, label="object "+str(kalman_id))
            fig.canvas.draw() #refreash the figure (NOTE: maybe not necessary)
            #fig.canvas.flush_events()
               
def euclidean_distance(p1, p2):
    """
    return the euclidian distance between two points 
    """
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)



class kalman():
    
    def __init__(self, classID, objectID):
        """
        Kalman class for asynchronous measurements.
        Args : 
            classID : class ID of the target
            objectID : object ID of the target 
        """
        self.classID = classID                          #class of the target 
        self.objectID = objectID                        #ID of the object
        self.t = 0.0                                    #time to start Kalman
        self.dt = 0.0                                   #interval of time between 2 observations
        self.KF = KalmanFilter(dim_x=4, dim_z=2)        #Kalman filter from filterpy 
        self.KF.x = np.array([0., 0., 0., 0.])          # initial state (location, velocity)
        self.KF.F = np.array([[1.,0., self.dt, 0.],
                                [0.,1., 0., self.dt],
                                [0.,0., 1., 0.],
                                [0.,0., 0., 1.]])       # state transition matrix
        self.KF.H = np.array([[1.,0., 0., 0.],
                                [0.,1., 0., 0.]])       # Measurement function (only position)
        self.KF.P *= 30.                                # covariance matrix (already define as np.eye(dim_x))
        self.KF.R = np.array([[1.,0.],
                                [0., 1.]])              # state uncertainty
        self.KF.Q = np.eye(4)
        self.state = self.KF.x                          # state of the traget
        self.statetoplot = deque([[0,0]]*10, maxlen=10) #variable to keep the ten last states 
             
    def process_kalman(self, position):
        self.KF.predict() # Prediction step
        reception_t = time.time()
        x = position[0]
        y = position[1]
        if(self.t == 0): #first observation
            self.KF.x = np.array([x, y, 0, 0]) # initial state (location, velocity)
        if(self.t != 0):
            reception_t = time.time() 
            self.dt = reception_t - self.t #compute the interval of time between two observation
            self.KF.F = np.array([[1.,0., self.dt, 0.],
                        [0.,1., 0., self.dt],
                        [0.,0., 1., 0.],
                        [0.,0., 0., 1.]])          # update state transition matrix
            self.KF.Q = np.eye(4)*self.dt
            obs = np.array([x, y])
            self.KF.update(obs)
        self.t = reception_t #reset the reception time
        self.state = self.KF.x #reset state
        #send the 10 last state to plot
        #self.statetoplot.appendleft([self.state[0], self.state[1]])
        #xstate = [x[0] for x in self.statetoplot]
        #ystate = [x[1] for x in self.statetoplot]
        return [self.state[0], self.state[1], str(self.classID)+"_"+str(self.objectID)]
        
