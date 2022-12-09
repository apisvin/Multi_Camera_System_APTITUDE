
from numpy import pi, cos, sin
from agent.car_modules.spi_helper import spi_ask, bytes_to_int
from usefull import limit_angle

radius = 0.023
axis = 0.236

class odometers:
  def __init__(self, spi):
    self.spi = spi
    self.x = 0
    self.y = 0
    self.theta = 0
    self.lastCountLeft = 0
    self.lastCountRight = 0

  def reset(self):
    self.x = 0
    self.y = 0
    self.theta = 0
    self.lastCountLeft = 0
    self.lastCountRight = 0

    spi_ask(self.spi,0x7F)

  def update(self):
    # SPi request
    countL = -bytes_to_int(spi_ask(self.spi, 0x13))
    countR = bytes_to_int(spi_ask(self.spi, 0x14))

    # Delta tick
    deltaL = countL - self.lastCountLeft
    deltaR = countR - self.lastCountRight

    self.lastCountLeft = countL
    self.lastCountRight = countR

    # delta displacement and rotation
    dS = (deltaR + deltaL) * 2 * pi * radius / (2 * 4 * 2048 )
    dTheta = (deltaR - deltaL) * 2 * pi * radius / (axis * 4 * 2048 )

    # Integrate it in position
    self.x += dS * cos(self.theta + dTheta/2)
    self.y += dS * sin(self.theta + dTheta/2)
    self.theta = limit_angle(self.theta + dTheta)

