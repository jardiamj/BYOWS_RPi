# BYOWS_RPI : WeeWx Driver Implementation of the Build your own WeatherStation Guide Produced by the Raspberry Pi Organization
# GitHub repo: https://github.com/jardiamj/BYOWS_RPi
# Copywrite 2019 Jardi Martinez
# WeeWX Package prepared by Doug Jenkins

import configobj
from setup import ExtensionInstaller
from io import StringIO


# ----- Extension Information -----
VERSION = "0.51"
NAME = 'byows_rpi'
PACKAGE_DESCRIPTION = 'Bring Your Own Weather Station (BYOWS) Driver for the Raspberry Pi'
AUTHOR = "Jardi Martinez"
AUTHOR_EMAIL = "https://github.com/jardiamj/BYOWS_RPi"

# ----- Extension File List -----
filelist = [('bin/user', ['bin/user/byows_rpi.py'])]

# ----- Configuration details for Weewx.conf -----

driver_config = """

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

"""

config_dict = configobj.ConfigObj(StringIO(driver_config))


# ----- Extension Loader (Using Generic WeeWX Extension Installer) -----
def loader():
    return WeeEXTInstaller()


class WeeEXTInstaller(ExtensionInstaller):
    def __init__(self):
        super(WeeEXTInstaller, self).__init__(
            version=VERSION,
            name=NAME,
            description=PACKAGE_DESCRIPTION,
            author=AUTHOR,
            author_email=AUTHOR_EMAIL,
            files=filelist,
            config=config_dict
        )