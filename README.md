byows_rpi - This is an weeWX driver implementation of the Build Your OWN Weather
Station using the Raspberry Pi: 
https://projects.raspberrypi.org/en/projects/build-your-own-weather-station/

Copyright 2019 Jardi A. Martinez Jordan
Distributed under terms of the GPLv3

===============================================================================
Installation:

Download the byows_rpi.py file and copy it to your weeWX user directory.
In Debian it is: /usr/share/weeWX/user

You could install the driver by using git to clone the project into the weewx user folder:
    
    git clone https://github.com/jardiamj/BYOWS_RPI.git .
    
That will also copy a directory named "files", those files are not necessary for
the driver to work, they are there for my own documenting purposes.

For now you will have to edit the weewx.conf file in order to use this driver.
I'll build a configurator class for it later on.

-------------------------Manuall configuration-------------------------------------------
Modify your /etc/weewx/weewx.conf fiel to use the byows_rpi driver by writing:
station-type = BYOWS under [Station], like this:

[Station]  
    ...
    # Set to type of station hardware. There must be a corresponding stanza
    # in this file with a 'driver' parameter indicating the driver to be used.
    station_type = BYOWS
    
Add a section in the weewx.conf file for the wmII driver, it should look like this:
The only required variable is driver = user.byows_rpi. All the others are optional
the DEFAULT values are the ones from the BYOWS guide in the raspberry pi website.

If you are using different hardware or connecting them to a different pin or port
you will need to set that option here.

[BYOWS]
    # This section is for the Raspberry Pi Bring Your Own Weather Station driver.
       
    # The driver to use.
    driver = user.byows_rpi

    # How often should the driver generate packets in seconds
    loop_interval = 2.5

    # Pin to which anemometer is connected, the DEFAULT is pin 5.
    anemometer_pin = 5
    
    # Pin to which rain bucket is connected, the DEFAULT is pin 6.
    rain_bucket_pin = 6
    
    # Port and address for sensor bme280, the DEFAULT are port=1 address=0x77
    bme280_port = 1
    bme280_address = 0x77
    
    # Channel to which wind vane is connected to on MCP3008, The DEFAULT is channel 0
    mcp3008_channel = 0
    
    # Anemometer adjustment value, the DEFAULT is 1.18
    anemometer_adjustment = 1.18
    
    # Bucket Size in mm, the DEFAULT is 0.2794 mm.
    bucket_size = 0.2794
    
    # Anemometer radious in cm, the DEFAULT is 9.0 cm.    
    anemometer_radius_cm = 9.0