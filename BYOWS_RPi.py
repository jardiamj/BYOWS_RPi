from gpiozero import Button
import time
import math
import bme280_sensor_2
import wind_direction_byo_5
import statistics
import ds18b20_therm
import datetime
import database

wind_interval = 1 # How often (secs) to sample speed
interval = 5 # measurements recorded every 5 seconds
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600
ADJUSTMENT = 1.18
BUCKET_SIZE = 0.2794

class BYO_RPi_Station(object):
    """ Object that represents a BYO_Station. """
    
    def __init__(self):
        """ Initialized Onject. """
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

station = BYO_RPi_Station() #This is how we'll pass our station object into the weeWX driver
temp_probe = ds18b20_therm.DS18B20()

db = database.weather_database()
store_speeds = []
store_directions = []

while True:
    start_time = time.time()
    while time.time() - start_time <= interval:
        wind_start_time = time.time()
        station.reset_wind()
        # time.sleep(1)
        while time.time() - wind_start_time <= wind_interval:
           store_directions.append(wind_direction_byo_5.get_value())

        final_speed = station.calculate_speed(wind_interval)# Add this speed to the list
        store_speeds.append(final_speed)
    wind_average = wind_direction_byo_5.get_average(store_directions)
    wind_gust = max(store_speeds)
    wind_speed = statistics.mean(store_speeds)
    rainfall = station.get_rainfall()
    store_speeds = []
    store_directions = []

    ground_temp = temp_probe.read_temp()
#    ground_temp =45 
    humidity, pressure, ambient_temp = bme280_sensor_2.read_all()
#    db.insert(ambient_temp, ground_temp, 0, pressure, humidity, wind_average, wind_speed, wind_gust, rainfall)
    db.insert(ambient_temp, ground_temp, 0, pressure, humidity, wind_average, wind_speed, wind_gust, rainfall, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    print('Wind direction: ' + str(wind_average) +' /', 'Wind speed: ' + str(wind_speed) +' /', 'Wind gust: ' + str(wind_gust) +' /', 'Rainfall: ' + str(rainfall) +' /', 'Humidity: ' + str(humidity) +' /', 'Pressure: ' + str(pressure) +' /', 'Ambient Temperature: ' + str(ambient_temp)  +' /', 'Ground Temperature: ' +str(ground_temp) +';')
    print()

