

# Perform spi request on addr (only read)
def spi_ask(spi, addr):
  fromSpi = spi.xfer2([addr, 0xFF, 0xFF, 0xFF, 0xFF])

  return [int(v) for v in fromSpi[1:]]

# Two complement of given value
def twos_comp(val, bits):
  """compute the 2's complement of int value val"""
  if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
      val = val - (1 << bits)        # compute negative value
  return val

# Convert a list of byte to int
def bytes_to_int(bytes):
  intValue = 0
  for idx, byte in enumerate(bytes):
    intValue += byte * (256)** (len(bytes)-1-idx)
  return twos_comp(intValue,8*len(bytes))
