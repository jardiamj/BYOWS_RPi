# Introduction

byows_rpi - This is an weeWX driver implementation of the Build Your Own Weather
Station guide produced by the [Raspberry Pi Organization](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/)

Copyright 2019 Jardi A. Martinez Jordan
Distributed under terms of the GPLv3

# Installation

download the latest release (v0.51) from GitHub into your WeeWx directory
```
wget https://github.com/jardiamj/BYOWS_RPi/archive/refs/tags/v1.0.0.zip
```

Once it is downloaded, run the WeeWX Extension installer. This will install the driver and add the default configuration items to your WeeWX.conf file

```
sudo ./bin/wee_extension --install v1.0.0.zip
```


## Configuration

To enable the byows_rpi driver modify the weewx.conf file and change 
the "station_type" variable to "BYOWS" in the "[Station]" section. Configure the driver by looking for the BYOWS stanza at the end of the file.


If you are using different hardware or connecting them to a different pin or port, you are able
to add additional variables in the "[BYOWS]" section and thereby overwriting the default values in
the byows_rpi driver.

Optional parameters configurable in the "[BYOWS]" Section:

* **loop_interval** : How often should the driver generate packets in seconds. Default is 2.5 seconds
* **anemometer_pin** : Pin to which anemometer is connected, the DEFAULT is pin 5.
* **rain_bucket_pin** : Pin to which rain bucket is connected, the DEFAULT is pin 6.
* **bme280_port** : port for sensor bme280. The default value is 1
* **bme280_address** : The address for sensor bme280. The default address is 0x77
* **mcp3008_channel** : Channel to which wind vane is connected to on MCP3008, The DEFAULT is channel 0
* **anemometer_adjustment** : Anemometer adjustment value, the DEFAULT is 1.18
* **bucket_size** : Bucket Size in mm, the DEFAULT is 0.2794 mm.
* **anemometer_radius_cm** : Anemometer radius in cm, the DEFAULT is 9.0 cm.    
