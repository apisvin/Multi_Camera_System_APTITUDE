from low_level import Motor
from odomerty import odometers
from encoders import encoders
from middle_level import compute_speed
from time import sleep, time
from random import randrange
from dijkstra import Graph

# List of point defining a trajectory.
# First value is the x position
# Second value is the y position
# Expressed in meter
listOfPos = [
    (0,0),
    (0.5,0),
    (0.5,0.5),
    (0,0.5),
    (-0.5,0.5),
    (-0.5,0),
    (-0.5,-0.5),
    (0,-0.5),
    (0.5,-0.5),
    (0,0.1)
]



def fix_target(previous_target, actual_target, forbidden_target, graph):
    neighbourhood = graph[actual_target]["neighbourhood"]
    ft = []
    ft.append(previous_target)
    ft.append(forbidden_target)
    for t in ft:
        print(t)
        if(t in neighbourhood):
            print("Node " + t +" is not reachable")
            neighbourhood.remove(t)
    print("possible target", neighbourhood)  
    futur_target = neighbourhood[randrange(len(neighbourhood))-1]
    return actual_target, futur_target

def go_to_target(previous_target, actual_target, final_target, odos, encs, motLeft, motRight):
    position = {
    "A" : (0.5, -0.5),
    "B" : (0.5, 0.0),
    "C" : (0.5, 0.5),
    "D" : (0.0, -0.5),
    "E" : (0.0, 0.0),
    "F" : (0.0, 0.5),
    "G" : (-0.5, -0.5),
    "H" : (-0.5, 0.0),
    "I" : (-0.5, 0.5)}

    objectivePos = position[actual_target]
    # Compute position and error
    odos.update()
    errX = objectivePos[0] - odos.x
    errY = objectivePos[1] - odos.y

    # Compute wheel speed and apply it
    (omegaLeft, omegaRight) = compute_speed(errX, errY,odos.theta)
    encs.update()
    motLeft.set_objective_speed(encs.omegaL, omegaLeft)
    motRight.set_objective_speed(encs.omegaR, omegaRight)

    # Debug at low frequency
    if i == 500 and DEBUG:
      print(odos.x,odos.y,odos.theta)
      print("L", encs.omegaL, omegaLeft)
      print("L", encs.omegaR, omegaRight)
      print(atan2(errY, errX))
      i = 0
    else:
      i+= 1

    # Compute distance to target and fetch next one
    d = (errX)**2 + (errY)**2
    if d < 0.0025:
      dijkstra = DijkstraSPF(graph, actual_target)
      previous_target = dijkstra.get_path(final_target)[0]
      actual_target = dijkstra.get_path(final_target)[1]
      print("Previous target", previous_target)
      print("New target", actual_target)
      return previous_target