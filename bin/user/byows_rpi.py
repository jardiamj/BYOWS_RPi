#!/usr/bin/env python
"""
Copyright 2019 Jardi A. Martinez Jordan <jardiamj@gmail.com>

This is an weeWX driver implementation of the Build Your OWN Weather
Station using the Raspberry Pi:
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
import logging  #This supports the new WeeWX 4.x logging methodology
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

DRIVER_NAME = "BYOWS"
DRIVER_VERSION = "0.51"

#Initialize the logger for this module
log = logging.getLogger(__name__)

def loader(config_dict, _):
    return ByowsRpi(**config_dict[DRIVER_NAME])


"""
def confeditor_loader():
    return ByowsRpiConfEditor()
"""


class ByowsRpi(weewx.drivers.AbstractDevice):
    """weewx driver for the Build Your Own Weather Station - Raspberry Pi

    """

    def __init__(self, **stn_dict):
        self.hardware = stn_dict.get("hardware", "BYOWS - Raspberry Pi")
        self.loop_interval = float(stn_dict.get("loop_interval", 5))
        params = dict()
        params["anem_pin"] = int(stn_dict.get("anemometer_pin", 5))
        params["rain_bucket_pin"] = int(stn_dict.get("rain_bucket_pin", 6))
        params["bme280_port"] = int(stn_dict.get("bme280_port", 1))
        params["bme280_address"] = int(stn_dict.get("bme280_address", "0x77"), 16)
        params["mcp3008_channel"] = int(stn_dict.get("mcp3008_channel", 0))
        params["anem_adjustment"] = float(stn_dict.get("anemometer_adjustment", 1.18))
        params["bucket_size"] = float(stn_dict.get("bucket_size", 0.2794))
        params["anem_radius_cm"] = float(stn_dict.get("anemometer_radius_cm", 9.0))
        log.info("using driver %s" % DRIVER_NAME)
        log.info("driver version is %s" % DRIVER_VERSION)
        self.station = ByowsRpiStation(**params)

    @property
    def hardware_name(self):
        return self.hardware

    def genLoopPackets(self):
        """ Function that generates packets for weeWX by looping through station
        data generator function. """
        while True:
            packet = {"dateTime": int(time.time() + 0.5), "usUnits": weewx.METRIC}
            data = self.station.get_data()
            packet.update(data)
            yield packet
            time.sleep(self.loop_interval)  # defaults to 5 seconds


class ByowsRpiStation(object):
    """ Object that represents a BYOWS_Station. """

    CM_IN_A_KM = 100000.0
    SECS_IN_AN_HOUR = 3600

    def __init__(self, **params):
        """ Initialize Object. """
        self.bme280_address = params.get("bme280_address")
        self.bme280_bus = smbus2.SMBus(params.get("bme280_port"))
        self.bme280_sensor = bme280
        self.bme280_sensor.load_calibration_params(self.bme280_bus, self.bme280_address)
        self.bucket_size = params.get("bucket_size")  # in mm
        self.rain_count = 0
        self.wind_gauge = WindGauge(
            params.get("mcp3008_channel"),
            params.get("anem_pin"),
            params.get("anem_radius_cm"),
            params.get("anem_adjustment"),
        )
        self.rain_sensor = Button(params.get("rain_bucket_pin"))
        self.rain_sensor.when_pressed = self.bucket_tipped
        self.temp_probe = DS18B20()

    def bucket_tipped(self):
        self.rain_count = self.rain_count + 1

    def get_bme280_data(self):
        try:
            data = self.bme280_sensor.sample(self.bme280_bus, self.bme280_address)
            humidity = data.humidity
            pressure = data.pressure
            temperature = data.temperature
        except:
            log.debug("Error sampling sensor bme280, passing None as data.")
            humidity, pressure, temperature = None, None, None
            pass
        return humidity, pressure, temperature

    def get_soil_temp(self):
        return self.temp_probe.read_temp()

    def get_rainfall(self):
        """ Returns rainfall in cm. """
        rainfall = (self.rain_count * self.bucket_size) / 10.0
        self.reset_rainfall()
        return rainfall

    def get_data(self):
        """ Generates data packets every time interval. """
        data = dict()
        anem_rotations = self.wind_gauge.wind_count / 2.0
        time_interval = self.wind_gauge.last_wind_time - time.time()
        wind_speed, wind_dir = self.wind_gauge.get_wind()
        humidity, pressure, ambient_temp = self.get_bme280_data()
        data["outHumidity"] = humidity
        data["pressure"] = pressure
        data["outTemp"] = ambient_temp
        data["soilTemp1"] = self.get_soil_temp()
        data["windSpeed"] = float(wind_speed)
        data["windDir"] = wind_dir
        data["rain"] = float(self.get_rainfall())
        data["anemRotations"] = anem_rotations
        data["timeAnemInterval"] = time_interval
        return data

    def reset_rainfall(self):
        self.rain_count = 0


class DS18B20(object):
    """
    add the lines below to /etc/modules (reboot to take effect)
    w1-gpio
    w1-therm
    """

    def __init__(self):
        w1_devices = glob.glob("/sys/bus/w1/devices/28*")
        self.device_file = w1_devices[0] + "/w1_slave" if len(w1_devices) > 0 else None

    def read_temp_raw(self):
        if self.device_file != None:
            f = open(self.device_file, "r")
            lines = f.readlines()
            f.close()
            return lines
        else:
            return None

    def crc_check(self, lines):
        if len(lines[0].strip()) > 0:
            return lines[0].strip()[-3:] == "YES"
        else:
            return False

    def read_temp(self):
        temp_c = -255
        attempts = 0

        lines = self.read_temp_raw()

        if lines != None:
            success = self.crc_check(lines)

            while not success and attempts < 3:
                time.sleep(0.2)
                lines = self.read_temp_raw()
                success = self.crc_check(lines)
                attempts += 1

            if success:
                temp_line = lines[1]
                equal_pos = temp_line.find("t=")
                if equal_pos != -1:
                    temp_string = temp_line[equal_pos + 2 :]
                    temp_c = float(temp_string) / 1000.0

            return temp_c
        else:
            return None


class WindGauge(object):
    """ Object that represents a Wind Vane sensor. """

    WIND_VANE_VOLTS = {
        0.4: 0.0,
        1.4: 22.5,
        1.2: 45.0,
        2.8: 67.5,
        2.7: 90.0,
        2.9: 112.5,
        2.2: 135.0,
        2.5: 157.5,
        1.8: 180.0,
        2.0: 202.5,
        0.7: 225.0,
        0.8: 247.5,
        0.1: 270.0,
        0.3: 292.5,
        0.2: 315.0,
        0.6: 337.5,
    }
    CM_IN_A_KM = 100000.0
    SECS_IN_AN_HOUR = 3600

    def __init__(self, channel=0, anem_pin=5, anem_radius=9.0, anem_adjustment=1.18):
        # pass channel of MCP3008 where wind vane is connected to
        self.adc = MCP3008(channel)
        self.wind_count = 0  # Counts how many half-rotations
        self.last_wind_time = time.time()
        self.wind_speed_sensor = Button(anem_pin)
        self.wind_speed_sensor.when_pressed = self.spin
        self.anemometer_radius_cm = anem_radius  # Radius of your anemometer
        self.anemometer_adjustment = anem_adjustment

    # Every half-rotations, add 1 to count
    def spin(self):
        self.wind_count = self.wind_count + 1

    def reset_wind(self):
        self.wind_count = 0
        self.last_wind_time = time.time()

    def get_wind_speed(self):
        """ Function that returns wind speed in km/hr. """
        wind_speed = self.calculate_speed(time.time() - self.last_wind_time)
        self.reset_wind()  # reset wind_count and last time reading
        return wind_speed

    def get_wind(self, length=5):
        """ Function that returns wind as a vector: speed, direction."""
        return self.get_wind_speed(), self.read_direction()

    def calculate_speed(self, time_sec):
        circumference_cm = (2 * math.pi) * self.anemometer_radius_cm
        rotations = self.wind_count / 2.0
        # Calculate distance travelled by a cup in km
        dist_km = (circumference_cm * rotations) / self.CM_IN_A_KM
        # Speed = distance / time
        km_per_sec = dist_km / time_sec
        km_per_hour = km_per_sec * self.SECS_IN_AN_HOUR
        # Calculate Speed
        final_speed = km_per_hour * self.anemometer_adjustment
        return final_speed

    def read_direction(self):
        wind = round(self.adc.value * 3.3, 1)
        if not wind in self.WIND_VANE_VOLTS:  # keep only good measurements
            log.debug("Unknown Wind Vane value: %s" % str(wind))
            return None
        else:
            return self.WIND_VANE_VOLTS[wind]

    def get_average_direction(self, length=5):
        # Get the average wind direction in a length of time in seconds
        data = []
        # print("Measuring wind direction for %d seconds..." % length)
        start_time = time.time()
        while time.time() - start_time <= length:
            direction = self.read_direction()
            if direction is not None:
                data.append(direction)
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
if __name__ == "__main__":
    station = ByowsRpiStation()
    packet = {"dateTime": int(time.time() + 0.5), "usUnits": weewx.METRIC}

    interval = 5

    data = station.get_data(interval)  # defaults to 5 seconds
    packet.update(data)
    print(packet)
