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

# Imports specific for ByowsRpiStation class
from gpiozero import Button, MCP3008
import os, glob
import bme280
import smbus2

import weewx.drivers

DRIVER_NAME = 'BYOWS'
DRIVER_VERSION = '0.2'


def loader(config_dict, _):
    return ByowsRpi(**config_dict[DRIVER_NAME])

"""
def confeditor_loader():
    return ByowsRpiConfEditor()
"""

def logmsg(level, msg):
    syslog.syslog(level, 'BYOWS RPi: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)
  
    
class ByowsRpi(weewx.drivers.AbstractDevice):
    """weewx driver for the Build Your Own Weather Station - Raspberry Pi
    
    """
    def __init__(self, **stn_dict):
        self.hardware = "BYOWS - Raspberry Pi"
        loginf('using driver %s' % DRIVER_NAME)
        loginf('driver version is %s' % DRIVER_VERSION)
        self.station = ByowsRpiStation()
        
    @property
    def hardware_name(self):
        return self.hardware
    
    def genLoopPackets(self):
        """ Function that generates packets for weeWX by looping through station
        data generator function. """
                         
        for data in self.station.data:
            packet = {'dateTime': int(time.time() + 0.5),
                    'usUnits': weewx.METRIC}
            packet.update(data)
            
            yield packet


class ByowsRpiStation(object):
    """ Object that represents a BYOWS_Station. """
    CM_IN_A_KM = 100000.0
    SECS_IN_AN_HOUR = 3600
    ADJUSTMENT = 1.18
    BUCKET_SIZE = 0.2794
    ANEMOMETER_RADIUS_CM = 9.0 # Radius of your anemometer
    def __init__(self):
        """ Initialize Object. """
        bme280_port = 1
        self.bme280_address = 0x76 
        self.bme280_bus = smbus2.SMBus(bme280_port)
        self.bme280_sensor = bme280
        self.bme280_sensor.load_calibration_params(self.bme280_bus,
                                                   self.bme280_address)
        self.wind_count = 0 # Counts how many half-rotations
        self.rain_count = 0
        self.wind_speed_sensor = Button(5)
        self.wind_speed_sensor.when_pressed = self.spin
        self.rain_sensor = Button(6)
        self.rain_sensor.when_pressed = self.bucket_tipped
        self.wind_vane = WindVane(channel=0)
        self.temp_probe = DS18B20()
        self.data = self.get_data() #generator function you can loop through

    # Every half-rotations, add 1 to count
    def spin(self):
        self.wind_count = self.wind_count + 1
        
    def bucket_tipped(self):
        self.rain_count = self.rain_count + 1
        
    def get_bme280_data(self):
        try:
            data = self.bme280_sensor.sample(self.bme280_bus,self.bme280_address)
            humidity, pressure, temperature = data.humidity, data.pressure, data.temperature
        except:
            logdbg("Error sampling sensor bme280, passing None as data.")
            humidity, pressure, temperature = None, None, None
            pass
        return humidity, pressure, temperature
        
    def get_soil_temp(self):
        return self.temp_probe.read_temp()
        
    def get_wind(self,length=5):
        """ Function that returns wind as a vector (speed, direction) in a
        period of time (length) in seconds. """
        self.reset_wind()
        wind_direction = self.wind_vane.get_value(length) # runs for interval seconds
        wind_speed = self.calculate_speed(length)
        return wind_speed, wind_direction
        
    def get_wind_direction(self):
        return self.wind_vane.read_direction()
        
    def get_wind_speed(self,time_sec):
        wind_speed = self.calculate_speed(time_sec)
        self.reset_wind()
        return wind_speed

    def calculate_speed(self, time_sec):
        circumference_cm = (2 * math.pi) * self.ANEMOMETER_RADIUS_CM
        rotations = self.wind_count / 2.0
        # Calculate distance travelled by a cup in km
        dist_km = (circumference_cm * rotations) / self.CM_IN_A_KM
        # Speed = distance / time
        km_per_sec = dist_km / time_sec
        km_per_hour = km_per_sec * self.SECS_IN_AN_HOUR
        # Calculate Speed
        final_speed = km_per_hour * self.ADJUSTMENT
        return final_speed
    
    def get_rainfall(self):
        rainfall = self.rain_count * self.BUCKET_SIZE
        self.reset_rainfall()
        return rainfall
        
    def get_data(self):
        """ Generates data packets every second. Rain packet gets generated only
        if there are any rain clicks registered and windSpeed gets generated
        every 5 packet loops (about 5 seconds). """
        while True:
            data = dict()
            interval = 0
            for x in range(5): # will run for about 5 seconds
                start_time = time.time()
                time.sleep(1) # get values every 1 second
                humidity, pressure, ambient_temp = self.get_bme280_data()
                data['outHumidity'] = humidity
                data['pressure'] = pressure
                data['outTemp'] = ambient_temp
                data['soilTemp1'] = self.get_soil_temp()
                data['windDir'] = self.get_wind_direction()
                x += 1
                interval += time.time() - start_time # acumulates elapsed time
                yield data
                       
            if self.rain_count > 0: # generate rain only if bucket has been tipped
                rainfall = self.get_rainfall()
                data['rain'] = rainfall
            
            wind_speed = self.get_wind_speed(interval) # every 5 seconds
            data['windSpeed'] = float( wind_speed )
            yield data

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
    WIND_VANE_VOLTS = { 0.4: 0.0,   1.4: 22.5,  1.2: 45.0,  2.8: 67.5,
                    2.7: 90.0,  2.9: 112.5, 2.2: 135.0, 2.5: 157.5,
                    1.8: 180.0, 2.0: 202.5, 0.7: 225.0, 0.8: 247.5,
                    0.1: 270.0, 0.3: 292.5, 0.2: 315.0, 0.6: 337.5}
    def __init__(self,channel=0):
        # pass channel of MCP3008 where wind vane is connected to
        self.count = 0
        self.adc = MCP3008(channel)
        
    def read_direction(self):
        wind =round(self.adc.value*3.3,1)
        if not wind in self.WIND_VANE_VOLTS: # keep only good measurements
            return None
        else:
            return self.WIND_VANE_VOLTS[wind]
        
    def get_value(self, length=5):
        # Get the average wind direction in a length of time in seconds
        data = []
        print("Measuring wind direction for %d seconds..." % length)
        start_time = time.time()
        while time.time() - start_time <= length:
            data.append(self.read_direction())
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

""" Section for testing purposes, so file can be run outside of weeWX. 
    invoke this as follows from the weewx root dir:
    PYTHONPATH=bin python bin/weewx/drivers/byows_rpi.py"""
if __name__ == '__main__':
    station = ByowsRpiStation()
    packet = {'dateTime': int(time.time() + 0.5),
              'usUnits': weewx.METRIC}
                      
    interval = 0
    
    for x in range(5):
        start_time = time.time()
        time.sleep(1)
        ground_temp = station.get_soil_temp()
        humidity, pressure, ambient_temp = station.get_bme280_data()
        wind_direction = station.get_wind_direction()
        
        packet['outTemp'] = float( ambient_temp )
        packet['outHumidity'] = float( humidity )
        packet['soilTemp1'] = float( ground_temp )
        packet['pressure'] = float( pressure )
        packet['windDir'] = wind_direction
        x += 1
        interval += time.time() - start_time
        print packet
               
    wind_speed = station.get_wind_speed(interval)
    rainfall = station.get_rainfall()
    packet['rain'] = rainfall
    packet['windSpeed'] = float( wind_speed )
    print packet
