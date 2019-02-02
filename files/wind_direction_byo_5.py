import math
from gpiozero import MCP3008
import time

WIND_VANE_VOLTS = {  0.4: 0.0,   1.4: 22.5,  1.2: 45.0,  2.8: 67.5,  2.7: 90.0,
         2.9: 112.5, 2.2: 135.0, 2.5: 157.5, 1.8: 180.0, 2.0: 202.5, 0.7: 225.0,
         0.8: 247.5, 0.1: 270.0, 0.3: 292.5, 0.2: 315.0, 0.6: 337.5}

class WindVane(object):
    """ Object that represents a Wind Vane sensor. """
    def __init__(self,channel=0):
        # pass channel of MCP3008 where wind vane is connected to
        self.count = 0
        self.adc = MCP3008(channel)
        
    def get_value(self, length=5):
        # Get the average wind direction in a length of time in seconds
        data = []
        print("Measuring wind direction for %d seconds..." % length)
        start_time = time.time()
        while time.time() - start_time <= length:
            wind =round(self.adc.value*3.3,1)
            if not wind in WIND_VANE_VOLTS: # keep only good measurements
                print('unknown value ' + str(wind))
            else:
                data.append(WIND_VANE_VOLTS[wind])
        return self.get_average(data)
        
    def get_average(self, angles):
        # Function that returns the average angle from a list of values
        sin_sum = 0.0
        cos_sum = 0.0

        for angle in angles:
            r = math.radians(angle)
            sin_sum += math.sin(r)
            cos_sum += math.cos(r)
        flen = float(len(angles))
        s = sin_sum / flen
        c = cos_sum / flen
        arc = math.degrees(math.atan(s / c))
        average = 0.0

        if s > 0 and c > 0:
            average = arc
        elif c < 0:
            average = arc + 180
        elif s < 0 and c > 0:
            average = arc + 360

        return 0.0 if average == 360 else average


while True:
    wind_vane = WindVane(0)
    wind_direction = wind_vane.get_value(2)
    



