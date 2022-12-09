import RPi.GPIO as GPIO

def limit(value, bound):
  if -bound < value and value < bound:
    return value
  if value < -bound:
    return - bound
  return bound


class Motor:
  def __init__(self, PWM_pin, dir_pin):
    # Parameters
    self.kp = 2.5
    self.ki = 0.00001

    self.err_integ = 0
    self.alpha=0.9 # Limit for anti-windup

    self.u_max = 12 # V max apply on the motor

    # Setting GPIO to interact with motor
    GPIO.setup(PWM_pin, GPIO.OUT)
    self.PWM = GPIO.PWM(PWM_pin, 20000)
    self.PWM.start(0)
    GPIO.setup(dir_pin, GPIO.OUT)
    self.dir_pin = dir_pin
    self.reversed = 1


  def __del__(self):
    if self.PWM is not None:
      self.PWM.stop()

  def reset(self):
    self.err_integ = 0

  # Low level control
  def set_objective_speed(self, curr_speed, new_speed):
    err_speed = new_speed - curr_speed
    curr_err_integ = err_speed * self.ki
    self.err_integ += curr_err_integ
    u_consigne = self.kp * err_speed + self.err_integ


    #TODO antiwindup

    self.apply_u(limit(100 * u_consigne / self.u_max, 95))

  def apply_u(self,u_value):

    if self.reversed*u_value < 0:
      GPIO.output(self.dir_pin,False)
    else:
      GPIO.output(self.dir_pin,True)

    # avoid weird bhaviour for low value
    val = 0
    if abs(u_value) > 1e-2:
        val = abs(u_value)

    self.PWM.ChangeDutyCycle(val)
