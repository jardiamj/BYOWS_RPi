#!/usr/bin/env python
"""
Copyright 2018 Jardi A. Martinez Jordan <jardiamj@gmail.com>

This is an weeWX driver implementation of the Build Your OWN Weather
Station usin the Raspberry Pi: 
https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
import math
import syslog
import time
import datetime

# Imports specific for BYOWS_RPi
from gpiozero import Button, MCP3008
import os, glob
import bme280
import smbus2

import weewx.drivers

DRIVER_NAME = 'BYOWS'
DRIVER_VERSION = '0.1'

wind_interval = 1 # How often (secs) to sample speed
interval = 5 # measurements recorded every 5 seconds
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600
ADJUSTMENT = 1.18
BUCKET_SIZE = 0.2794
WIND_VANE_VOLTS = { 0.4: 0.0,   1.4: 22.5,  1.2: 45.0,  2.8: 67.5,
                    2.7: 90.0,  2.9: 112.5, 2.2: 135.0, 2.5: 157.5,
                    1.8: 180.0, 2.0: 202.5, 0.7: 225.0, 0.8: 247.5,
                    0.1: 270.0, 0.3: 292.5, 0.2: 315.0, 0.6: 337.5}

def loader(config_dict, _):
    return BYOWS_RPi(**config_dict[DRIVER_NAME])

"""
def confeditor_loader():
    return BYOWS_RPiConfEditor()
"""

def logmsg(level, msg):
    syslog.syslog(level, 'BYOWS RPi: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)
    
class BYOWS_RPi(weewx.drivers.AbstractDevice):
    """weewx driver for the Build Your Own Weather Station - Raspberry Pi
    
    """
    def __init__(self, **stn_dict):
        self.hardware = "BYOWS - Raspberry Pi"
        loginf('using driver %s' % DRIVER_NAME)
        loginf('driver version is %s' % DRIVER_VERSION)
        self.station = BYOWS_RPi_Station()
        self.temp_probe = DS18B20()
        
    @property
    def hardware_name(self):
        return self.hardware
    
    def genLoopPackets(self):
        while True:
            """ get_wind() fuction will run for interval seconds and that will
            allow rainfall clicks to acumulate for that amount of time before
            being read.
            """
            wind_speed, wind_direction = self.station.get_wind(interval)
            rainfall = self.station.get_rainfall()

            ground_temp = self.temp_probe.read_temp()
            humidity, pressure, ambient_temp = self.station.get_bm280_data()

            packet = {'dateTime': int(time.time() + 0.5),
                      'usUnits': weewx.METRIC}
  
            packet['outTemp'] = float( ambient_temp )
            packet['outHumidity'] = float( humidity )
            packet['soilTemp1'] = float( ground_temp )
            packet['pressure'] = float( pressure )
            packet['rain'] = rainfall
            packet['windDir'] = float( wind_direction )
            packet['windSpeed'] = float( wind_speed )

            yield packet

class BYOWS_RPi_Station(object):
    """ Object that represents a BYOWS_Station. """
    def __init__(self):
        """ Initialize Object. """
        bme280_port = 1
        self.bme280_address = 0x76 
        self.bme280_bus = smbus2.SMBus(bme280_port)
        self.bme280_sensor = bme280
        self.bme280_sensor.load_calibration_params(self.bme280_bus,self.bme280_address)
        
        self.wind_count = 0 # Counts how many half-rotations
        self.radius_cm = 9.0 # Radius of your anemometer
        self.rain_count = 0
       
        self.wind_speed_sensor = Button(5)
        self.wind_speed_sensor.when_pressed = self.spin
        self.rain_sensor = Button(6)
        self.rain_sensor.when_pressed = self.bucket_tipped
        self.wind_vane = WindVane(channel=0)

    # Every half-rotations, add 1 to count
    def spin(self):
        self.wind_count = self.wind_count + 1
        #print("spin" + str(wind_count))
        
    def get_bm280_data(self):
        data = self.bme280_sensor.sample(self.bme280_bus,self.bme280_address)
        return data.humidity, data.pressure, data.temperature
        
    def get_wind(self,length=5):
        self.reset_wind()
        wind_direction = self.wind_vane.get_value(length) # runs for interval seconds
        wind_speed = self.calculate_speed(length)
        return wind_speed, wind_direction

    def calculate_speed(self, time_sec):
        circumference_cm = (2 * math.pi) * self.radius_cm
        rotations = self.wind_count / 2.0
        # Calculate distance travelled by a cup in km
        dist_km = (circumference_cm * rotations) / CM_IN_A_KM
        # Speed = distance / time
        km_per_sec = dist_km / time_sec
        km_per_hour = km_per_sec * SECS_IN_AN_HOUR
        # Calculate Speed
        final_speed = km_per_hour * ADJUSTMENT
        return final_speed
    
    def get_rainfall(self):
        rainfall = self.rain_count * BUCKET_SIZE
        self.reset_rainfall()
        return rainfall

    def bucket_tipped(self):
        self.rain_count = self.rain_count + 1
        #print (rain_count * BUCKET_SIZE)

    def reset_rainfall(self):
        self.rain_count = 0

    def reset_wind(self):
        self.wind_count = 0


class DS18B20(object):
    """
    add the lines below to /etc/modules (reboot to take effect)
    w1-gpio
    w1-therm
    """
    def __init__(self):        
        self.device_file = glob.glob("/sys/bus/w1/devices/28*")[0] + "/w1_slave"
        
    def read_temp_raw(self):
        f = open(self.device_file, "r")
        lines = f.readlines()
        f.close()
        return lines
        
    def crc_check(self, lines):
        return lines[0].strip()[-3:] == "YES"
        
    def read_temp(self):
        temp_c = -255
        attempts = 0
        
        lines = self.read_temp_raw()
        success = self.crc_check(lines)
        
        while not success and attempts < 3:
            time.sleep(.2)
            lines = self.read_temp_raw()            
            success = self.crc_check(lines)
            attempts += 1
        
        if success:
            temp_line = lines[1]
            equal_pos = temp_line.find("t=")            
            if equal_pos != -1:
                temp_string = temp_line[equal_pos+2:]
                temp_c = float(temp_string)/1000.0
        
        return temp_c

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
        return get_average(data)
        
def get_average(angles):
    # Function that returns the average angle from a list of angles
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


