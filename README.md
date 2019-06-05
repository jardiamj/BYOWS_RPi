# Introduction

byows_rpi - This is an weeWX driver implementation of the Build Your Own Weather
Station guide produced by the [Raspberry Pi Organization](https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/)

Copyright 2019 Jardi A. Martinez Jordan
Distributed under terms of the GPLv3

# Installation

Download the byows_rpi.py file and copy it to your weeWX user directory.
In Debian it is: /usr/share/weewx/user

```
wget https://github.com/jardiamj/BYOWS_RPi/blob/master/byows_rpi.py -O /usr/share/weewx/user/byows_rpi.py
```

You could install the driver by using git to clone the project into the weewx user folder:

git clone https://github.com/jardiamj/BYOWS_RPI.git .
    
That will also copy a directory named "files", those files are not necessary for
the driver to work, they are there for my own documenting purposes.

## Configuration

To enable the byows_rpi driver modify the /etc/weewx/weewx.conf file and change 
the "station_type" variable to "BYOWS" in the "[Station]" section. Below is a snippet of the
configured station section.

```plaintext
[Station]  
    ...
    # Set to type of station hardware. There must be a corresponding stanza
    # in this file with a 'driver' parameter indicating the driver to be used.
    station_type = BYOWS
```
Then add an new section called "[BYOWS]" preferably below the "[Station]" section.

```plaintext
[BYOWS]
    # This section is for the Raspberry Pi Bring Your Own Weather Station driver.
    
    # [REQUIRED]
    # The driver to use.
    driver = user.byows_rpi
```

If you are using different hardware or connecting them to a different pin or port, you are able
to add additional variables in the "[BYOWS]" section and thereby overwriting the default values in
the byows_rpi driver. Please see 


```plaintext
[BYOWS]
    # This section is for the Raspberry Pi Bring Your Own Weather Station driver.

    # [REQUIRED]
    # The driver to use.
    driver = user.byows_rpi

    # [OPTIONAL]
    # How often should the driver generate packets in seconds
    loop_interval = 2.5

    # [OPTIONAL]
    # Pin to which anemometer is connected, the DEFAULT is pin 5.
    anemometer_pin = 5
    
    # [OPTIONAL]
    # Pin to which rain bucket is connected, the DEFAULT is pin 6.
    rain_bucket_pin = 6
    
    # [OPTIONAL]
    # Port and address for sensor bme280, the DEFAULT are port=1 address=0x77
    bme280_port = 1
    bme280_address = 0x77
    
    # [OPTIONAL]
    # Channel to which wind vane is connected to on MCP3008, The DEFAULT is channel 0
    mcp3008_channel = 0
    
    # [OPTIONAL]
    # Anemometer adjustment value, the DEFAULT is 1.18
    anemometer_adjustment = 1.18
    
    # [OPTIONAL]
    # Bucket Size in mm, the DEFAULT is 0.2794 mm.
    bucket_size = 0.2794
    
    # [OPTIONAL]
    # Anemometer radious in cm, the DEFAULT is 9.0 cm.    
    anemometer_radius_cm = 9.0
```
