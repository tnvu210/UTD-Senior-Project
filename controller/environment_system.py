import sys
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')
from aosong import am2315
import wiringpi
import logging

SENSOR = am2315.Sensor()
FAN_PIN = 3
LED_PIN = 2
DEHUMIDIFIER_PIN = 4
logger = logging.getLogger('garden.controller.environment_system')


def humidity_temp():
    logger.info('reading from temp humidity sensor')

    while True:
        try:
            reading = SENSOR.data()
        except (AssertionError, TypeError):
            continue
            logger.info('bad reading assertion or type error')
        else:
            if reading is None:
                logger.info('bad reading nonetype')
                continue
            else:
                break

    logger.info('reading successful')
    return reading


def lights_on():
    logger.info('turning lights on')
    wiringpi.digitalWrite(LED_PIN, 0)


def lights_off():
    logger.info('turning lights off')
    wiringpi.digitalWrite(LED_PIN, 1)


def dehumidifier_on():
    logger.info('turning dehumidifier on')
    wiringpi.digitalWrite(DEHUMIDIFIER_PIN, 0)


def dehumidifier_off():
    logger.info('turning dehumidifier off')
    wiringpi.digitalWrite(DEHUMIDIFIER_PIN, 1)


def fan_on():
    logging.info('turning fan on')
    wiringpi.digitalWrite(FAN_PIN, 0)


def fan_off():
    logging.info('turning fan off')
    wiringpi.digitalWrite(FAN_PIN, 1)

