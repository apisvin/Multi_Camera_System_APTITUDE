import numpy as np
import logging
import time
from agent.agent import Agent

#import for car 
from agent.car_modules.encoders import encoders
from agent.car_modules.low_level import Motor
from agent.car_modules.odomerty import odometers
from agent.car_modules.middle_level import compute_speed
from agent.car_modules.graph import Graph
from agent.car_modules.dijkstra import next_target
#import valid only on car
import RPi.GPIO as GPIO
import spidev

class car(Agent):
    
    def __init__(self, stopFlag, neighbourhood, dicqueue):
        """
        car.
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

        #init graph
        nodes = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
        init_graph = {}
        for node in nodes:
            init_graph[node] = {}
            
        init_graph["A"]["B"] = 2
        init_graph["B"]["C"] = 2
        init_graph["C"]["F"] = 2
        init_graph["F"]["I"] = 2
        init_graph["I"]["H"] = 2
        init_graph["H"]["G"] = 2
        init_graph["G"]["D"] = 2
        init_graph["D"]["A"] = 2

        init_graph["D"]["E"] = 3
        init_graph["B"]["E"] = 3
        init_graph["F"]["E"] = 3
        init_graph["H"]["E"] = 3

        self.graph = Graph(nodes, init_graph)

    def launch(self):
        # Condition initial : begin at E and go to I
        final_target = "I"
        previous_target = "E"
        target = next_target(start_node=previous_target, target_node=final_target, graph=self.graph)
        position = {"A" : (1.0, -1.0),
                    "B" : (1.0, 0.0),
                    "C" : (1.0, 1.0),
                    "D" : (0.0, -1.0),
                    "E" : (0.0, 0.0),
                    "F" : (0.0, 1.0),
                    "G" : (-1.0, -1.0),
                    "H" : (-1.0, 0.0),
                    "I" : (-1.0, 1.0)}
        absolutePos = [0,0]
        theta = 0
        obstacle = None
        while self.stopFlag.is_set()==False:
            objectivePos = position[target]
            last_pos = absolutePos
            # Compute position and error 
            try:
                msg = self.dicqueue.Qtocar.get(block=False)
                if(int(msg["spec"]["class_ID"])==0): #position of car
                    #information about position from cameras 
                    absolutePos = [ float(msg["spec"]["x"])/100, float(msg["spec"]["y"])/100 ]
                    if absolutePos != last_pos:
                        theta = np.arctan2( (absolutePos[1]-last_pos[1]) / (absolutePos[0]-last_pos[0]))
                    self.odos.update() #to update theta
                else: #anything else is a obstacle
                    obstacle = [ float(msg["spec"]["x"])/100, float(msg["spec"]["y"])/100 ]
            except:
                #no information from camers -> take odometers 
                self.odos.update()
                absolutePos = [self.odos.x, self.odos.y]
                theta = self.odos.theta
            
            errX = objectivePos[0] - absolutePos[0]
            errY = objectivePos[1] - absolutePos[1]

            # Compute wheel speed and apply it
            (omegaLeft, omegaRight) = compute_speed(errX, errY,theta)
            self.encs.update()
            self.motLeft.set_objective_speed(self.encs.omegaL, omegaLeft)
            self.motRight.set_objective_speed(self.encs.omegaR, omegaRight)

            # Compute distance to target and fetch next one
            d = (errX)**2 + (errY)**2
            if d < 0.02:
                # TODO compute dijkstra after modifying the graph with obstacle avoidance
                if obstacle is not None:
                    print("obstacle computed in graph")
                    n1, n2 = self.two_nearest_nodes(self.graph, position, obstacle)
                    logging.debug("no more edge between {} and {}".format(n1, n2))
                    self.graph.modify_weight(n1, n2, np.Infinity)
                previous_target = target
                # Change of final target
                if(previous_target == "I"):
                    final_target = "A"
                elif(previous_target == "A"):
                    final_target = "I"        
                # Update actual target
                print("start_node ", previous_target)
                print("target_node ", target)
                target = next_target(start_node=previous_target, target_node=final_target, graph=self.graph)


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

