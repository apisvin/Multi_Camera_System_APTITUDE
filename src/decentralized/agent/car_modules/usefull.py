from numpy import pi

# Limit angle in [-pi, pi]
def limit_angle(angle):
  val = angle
  while (val <= -pi):
    val+= 2 * pi
  while (val >= pi):
    val-= 2 * pi
  return val
