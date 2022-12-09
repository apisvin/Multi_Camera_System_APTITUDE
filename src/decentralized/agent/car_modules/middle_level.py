from math import sqrt, atan2, pi, fabs
from agent.car_modules.usefull import limit_angle

# Middle level parameters
thAngle = 10 * pi / 180
kforward = 3
kturn = 0.5

l = 0.09 # distance between wheels
radius = 0.023 # wheel radius

def compute_speed(errX, errY, theta):
  theta_err = limit_angle(atan2(errY,errX))
  angle = limit_angle(theta_err - theta)

  if fabs(angle) > thAngle:
    omegaRight = kturn * angle
    omegaLeft = -kturn * angle
  else :
    dist = sqrt(errX**2 + errY**2)
    omegaRight = kforward * dist + kturn * angle
    omegaLeft = kforward * dist - kturn * angle

  return (omegaLeft, omegaRight)
