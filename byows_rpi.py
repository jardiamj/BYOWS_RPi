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

import syslog
import time
import datetime

# Imports specific for BYOWS_RPi
from gpiozero import Button
import math
import bme280_sensor_2
import wind_direction_byo_5
import statistics
import ds18b20_therm

import weewx.drivers
import weewx.wxformulas

DRIVER_NAME = 'BYOWS'
DRIVER_VERSION = '0.1'

wind_interval = 1 # How often (secs) to sample speed
interval = 5 # measurements recorded every 5 seconds
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600
ADJUSTMENT = 1.18
BUCKET_SIZE = 0.2794

def loader(config_dict, _):
    return BYOWS_RPi(**config_dict[DRIVER_NAME])

"""
def confeditor_loader():
    return BYOWS_RPiConfEditor()
"""

def logmsg(level, msg):
    syslog.syslog(level, 'Weather Monitor II: %s' % msg)

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
        self.hardware = "BYOWS_RPi"
        loginf('using driver %s' % DRIVER_NAME)
        loginf('driver version is %s' % DRIVER_VERSION)

        self.station = BYO_RPi_Station()
        
    @property
    def hardware_name(self):
        return self.hardware
    
    def genLoopPackets(self):
        store_speeds = []
        store_directions = []
        temp_probe = ds18b20_therm.DS18B20()
        while True:
            start_time = time.time()
            while time.time() - start_time <= interval:
                wind_start_time = time.time()
                self.station.reset_wind()
                while time.time() - wind_start_time <= wind_interval:
                   store_directions.append(wind_direction_byo_5.get_value())

                final_speed = self.station.calculate_speed(wind_interval)# Add this speed to the list
                store_speeds.append(final_speed)
            wind_average = wind_direction_byo_5.get_average(store_directions)
            wind_gust = max(store_speeds)
            wind_speed = statistics.mean(store_speeds)
            rainfall = self.station.get_rainfall()
            store_speeds = []
            store_directions = []

            ground_temp = temp_probe.read_temp()
            humidity, pressure, ambient_temp = bme280_sensor_2.read_all()

            packet = {'dateTime': int(time.time() + 0.5),
                      'usUnits': weewx.METRIC}
  
            packet['outTemp'] = float( ambient_temp )
            packet['outHumidity'] = float( humidity )
            packet['soilTemp1'] = float( ground_temp )
            packet['pressure'] = float( pressure )
            packet['rain'] = rainfall
            packet['windDir'] = float( wind_average )
            packet['windSpeed'] = float( wind_speed )
            packet['windGust'] = float( wind_gust )

            yield packet


class BYO_RPi_Station(object):
    """ Object that represents a BYO_Station. """
    
    def __init__(self):
        """ Initialized Object. """
        self.wind_count = 0 # Counts how many half-rotations
        self.radius_cm = 9.0 # Radius of your anemometer
        self.rain_count = 0
        self.gust = 0

        self.wind_speed_sensor = Button(5)
        self.wind_speed_sensor.when_pressed = self.spin
        self.rain_sensor = Button(6)
        self.rain_sensor.when_pressed = self.bucket_tipped

    # Every half-rotations, add 1 to count
    def spin(self):
        self.wind_count = self.wind_count + 1
        #print("spin" + str(wind_count))


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

    def reset_gust(self):
        self.gust = 0


