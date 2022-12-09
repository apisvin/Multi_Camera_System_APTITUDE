import cv2
import numpy as np
import time
from agent.agent import Agent
from dijkstra import Graph, DijkstraSPF

#import for car 
from agent.car_modules.encoders import encoders
from agent.car_modules.low_level import Motor
from agent.car_modules.odomerty import odometers
from agent.car_modules.middle_level import compute_speed
#import valid only on car
import RPi.GPIO as GPIO
import spidev

class car(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        Detector is a detection agent. It has to process the video from camera in real time 
        or from a video file. It detects Aruco marker and return their coordinate at each frame in a
        global referential. The camera has to be calibrated.
        Args:
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
        """
        self.stopFlag= stopFlag
        self.dicqueue = dicqueue
        self.neighbourhood = neighbourhood

        #set parameters for robot 

        # Init motors
        GPIO.setmode(GPIO.BCM)
        self.motLeft = Motor(12,5)
        self.motRight = Motor(13,6)
        self.motRight.reversed = 1

        # Init SPI (for wheel speed and position)
        spi_cs=1
        spi = spidev.SpiDev()
        spi.open(0,spi_cs)
        spi.max_speed_hz=500000

        # Init odometers and encoders
        self.odos = odometers(spi)
        self.encs = encoders(spi)
        self.odos.reset()

        #init map
        self.A, self.B, self.C, self.D, self.E, self.F, self.G, self.H, self.I = self.nodes = list("ABCDEFGHI")
        self.graph = self.original_graph()

    def launch(self):
        # Condition initial : begin at E and go to I
        final_target = self.I
        dijkstra = DijkstraSPF(self.graph, self.E)
        previous_target = dijkstra.get_path(self.I)[0]
        actual_target = dijkstra.get_path(self.I)[1]
        position = {"A" : (0.5, -0.5),
                    "B" : (0.5, 0.0),
                    "C" : (0.5, 0.5),
                    "D" : (0.0, -0.5),
                    "E" : (0.0, 0.0),
                    "F" : (0.0, 0.5),
                    "G" : (-0.5, -0.5),
                    "H" : (-0.5, 0.0),
                    "I" : (-0.5, 0.5)}
        while self.stopFlag.is_set()==False:
            objectivePos = position[actual_target]
            # Compute position and error 
            try:
                msg = self.dicqueue.Qtocar.get(timeout = 0.5)
                #information about position from cameras 
                absolutePos = [ float(msg["spec"]["x"]), float(msg["spec"]["y"]) ]
                #reset odometers variable 
                self.odos.update() #to update theta

                self.odos.x = absolutePos[0]
                self.odos.y = absolutePos[1]
            except:
                #no information from camers -> take odometers 
                self.odos.update()
                absolutePos = [self.odos.x, self.odos.y]
            
            errX = objectivePos[0] - absolutePos[0]
            errY = objectivePos[1] - absolutePos[1]

            # Compute wheel speed and apply it
            (omegaLeft, omegaRight) = compute_speed(errX, errY,self.odos.theta)
            self.encs.update()
            self.motLeft.set_objective_speed(self.encs.omegaL, omegaLeft)
            self.motRight.set_objective_speed(self.encs.omegaR, omegaRight)

            # Compute distance to target and fetch next one
            d = (errX)**2 + (errY)**2
            if d < 0.0025:
                # TODO compute dijkstra after modifying the gra^ph with obstacle avoidance
                dijkstra = DijkstraSPF(self.graph, actual_target)
                previous_target = dijkstra.get_path(final_target)[0]
                # Change of final target
                if(previous_target == self.I):
                    final_target = self.A
                    dijkstra = DijkstraSPF(self.graph, previous_target)
                    previous_target = dijkstra.get_path(final_target)[0]
                elif(previous_target == self.A):
                    final_target = self.I         
                    dijkstra = DijkstraSPF(self.graph, previous_target)
                    previous_target = dijkstra.get_path(final_target)[0]
                # Update actual target
                actual_target = dijkstra.get_path(final_target)[1]
                print("Previous target", previous_target)
                print("New target", actual_target)

    def original_graph(self):
        graph = Graph()
        graph.add_edge(self.A, self.B, 1)
        graph.add_edge(self.B, self.A, 1)
        graph.add_edge(self.A, self.D, 1)
        graph.add_edge(self.D, self.A, 1)
        graph.add_edge(self.B, self.E, 2)
        graph.add_edge(self.E, self.B, 2)
        graph.add_edge(self.B, self.C, 1)
        graph.add_edge(self.C, self.B, 1)
        graph.add_edge(self.C, self.F, 1)
        graph.add_edge(self.F, self.C, 1)
        graph.add_edge(self.D, self.E, 2)
        graph.add_edge(self.E, self.D, 2)
        graph.add_edge(self.D, self.G, 1)
        graph.add_edge(self.G, self.D, 1)
        graph.add_edge(self.E, self.F, 2)
        graph.add_edge(self.F, self.E, 2)
        graph.add_edge(self.E, self.H, 2)
        graph.add_edge(self.H, self.E, 2)
        graph.add_edge(self.F, self.I, 1)
        graph.add_edge(self.I, self.F, 1)
        graph.add_edge(self.G, self.H, 1)
        graph.add_edge(self.H, self.G, 1)
        graph.add_edge(self.H, self.I, 1)
        graph.add_edge(self.I, self.H, 1)
        return graph

    def two_nearest_nodes(self, graph, trad, obstacle):
        distances = {}
        #compute distance between obstacle and each node 
        for node in graph.get_nodes():
            dist = np.sqrt((obstacle[0]-trad[str(node)][0])**2 + (obstacle[1]-trad[str(node)][1])**2)
            distances[str(node)] = dist
        #keep 2 nearest node
        temp = min(distances.values())
        [first] = [key for key in distances if distances[key] == temp]
        distances.pop(str(first))
        temp = min(distances.values())
        [second] = [key for key in distances if distances[key] == temp]
        return [first, second]

    def update_graph(self, graph, trad, obstacle):
        n1, n2 = self.two_nearest_nodes(graph, trad, obstacle)
        graph.add_edge(n1, n2, np.Infinity)
        graph.add_edge(n2, n1, np.Infinity)
        return graph


