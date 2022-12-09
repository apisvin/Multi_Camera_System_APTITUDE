from time import time
from numpy import pi
from spi_helper import spi_ask, bytes_to_int


class encoders:
  def __init__(self, spi):
    self.spi = spi
    self.omegaL = 0
    self.omegaR = 0


  def update(self):
    countL = -bytes_to_int(spi_ask(self.spi, 0x10))
    countR = bytes_to_int(spi_ask(self.spi, 0x11))

    self.omegaL = countL * 2 * pi / (81.92)
    self.omegaR = countR * 2 * pi / (81.92)
