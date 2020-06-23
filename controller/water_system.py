from controller import GardenDb
import sys
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')
import Adafruit_ADS1x15
import wiringpi
import time
import numpy
import logging

ADC = Adafruit_ADS1x15.ADS1115()
FLORAGROW_PIN = 7
FLORABLOOM_PIN = 15
FLORAMICRO_PIN = 16
PH_UP_PIN = 0
PH_DOWN_PIN = 1
ML_PER_SEC = 5 / 3
PERCENT_ERROR = .035
logger = logging.getLogger('garden.controller.water_system')


def _convert_adc_volts(reading, fsr):
    """fsr: full scale range of adc"""
    logger.info('converting adc value to voltage')
    adc_resolution = 32767
    return reading * (fsr / adc_resolution)


def _percent_error(ideal, actual):
    return abs(ideal - actual) / abs(ideal)


def _water_lvl():
    def voltage_to_resistance(voltage):
        return -(voltage * 560) / (voltage - 5)

    def resistance_to_inches(res):
        return (-7/1100)*res+(116/11)

    logger.info('reading water lvl from adc')
    reading = []
    for i in range(10):
        reading.append(ADC.read_adc(2, 1))
        time.sleep(0.25)

    volts = _convert_adc_volts(numpy.mean(reading), 4.096)
    logger.info(str(volts) + 'V')
    resistance = voltage_to_resistance(volts)
    return resistance_to_inches(resistance)


def gallons():
    logger.info('converting water level to gallons')
    gallons_per_cubic_inch = 0.004329
    volume = 15.9 * 23.9 * _water_lvl()
    return volume * gallons_per_cubic_inch


def ph():
    def volts_to_ph(volts):
        return 0.008217 * (volts**2) + 3.562 * volts - 0.191

    logger.info('reading ph voltage from adc')
    reading = []
    for i in range(10):
        reading.append(ADC.read_adc(0, 1))
        time.sleep(0.25)
    volts = _convert_adc_volts(numpy.mean(reading), 4.096)
    logger.info(str(volts) + 'V')
    return volts_to_ph(volts)


def ec():
    def volts_to_ec(volts):
        return 9.938992 * volts - 0.169312

    logger.info('reading ec from adc')
    reading = []
    for i in range(10):
        reading.append(ADC.read_adc(1, 1))
        time.sleep(0.5)
    volts = _convert_adc_volts(numpy.mean(reading), 4.096)
    logger.info(str(volts) + 'V')
    return volts_to_ec(volts)


def record_nutrient_log(grow, tiger, big_bloom, big_grow):
    GardenDb.db.get_conn()
    pump_log = GardenDb.PumpLog.create(grow_id=grow,
                            tiger_bloom_ml=tiger,
                            big_bloom_ml=big_bloom,
                            grow_ml=big_grow)
    pump_log.save()
    q = GardenDb.FeedingLog.insert(pump_log_id=pump_log)
    q.execute()
    GardenDb.db.close()


def pump(pin, amount):
    dispense_time = amount / ML_PER_SEC
    wiringpi.digitalWrite(pin, 0)
    time.sleep(dispense_time)
    wiringpi.digitalWrite(pin, 1)


def dispense_ph(ideal_ph, active_grow):
    def record_pump_log(amount, up_or_down):
        """up_or_down is a boolean True for up False for down"""
        GardenDb.db.get_conn()
        if up_or_down:
            GardenDb.PumpLog.insert(grow_id=active_grow,
                                    ph_up_ml=amount).execute()
        else:
            GardenDb.PumpLog.insert(grow_id=active_grow,
                                    ph_down_ml=amount).execute()
        logger.info('recorded amount dispensed to db')
        GardenDb.db.close()

    logger.info('checking current ph against ideal')
    reading = ph()

    if _percent_error(ideal_ph, reading) <= PERCENT_ERROR:
        # if ph is within error% of ideal do nothing
        logger.info('ph is within percent error. no action')
        pass
    else:
        # dispense 1 ml of solution per gallon
        logger.info('dispensing 1 ml of solution per gallon')

        if abs(reading-ideal_ph) > 2:
            if reading < 9:
                ml_per_gallon = 2
        else:
            ml_per_gallon = 1

        liquid = gallons()

        if reading < ideal_ph:
            pump(PH_UP_PIN, liquid * ml_per_gallon)
            record_pump_log(liquid * ml_per_gallon, True)
        else:
            pump(PH_DOWN_PIN, liquid * ml_per_gallon)
            record_pump_log(liquid * ml_per_gallon, False)


def pump_nutrients_full_feeding(active_grow):
    """full_feeding try to pump a total dose false to adjsut"""
    tea_spoon_ml = 5
    logger.info('dispense a full feeding dosage')
    # Calculate amount and time for flowering state
    floraGro_tea_per_gal = 1
    floraBloom_tea_per_gal = 1
    floraMicro_tea_per_gal = 1
    liquid = gallons()
    floraGro_dispense = (floraGro_tea_per_gal * tea_spoon_ml * liquid)
    floraBloom_dispense = (floraBloom_tea_per_gal * tea_spoon_ml * liquid)
    floraMicro_dispense = (floraMicro_tea_per_gal * tea_spoon_ml * liquid)

    # dispense tiger bloom
    pump(FLORAGROW_PIN, floraGro_dispense)
    # dispense big bloom
    pump(FLORABLOOM_PIN,floraBloom_dispense)
    # dispense big grow
    pump(FLORAMICRO_PIN, floraMicro_dispense)
    # log amount dispensed
    record_nutrient_log(active_grow, floraGro_dispense, floraBloom_dispense, floraMicro_dispense)


def pump_nutrients_adjust(ideal_ec, active_grow):
    tea_spoon_ml = 5
    reading = ec()
    if _percent_error(ideal_ec, reading) < PERCENT_ERROR:
        pass
    else:
        floraGrow_tea_per_gal = 0.5
        floraBloom_tea_per_gal = 0.5
        floraMicro_tea_per_gal = 0.5
        liquid = gallons()
        floraGrow_dispense = (floraGrow_tea_per_gal * tea_spoon_ml * liquid)
        floraBloom_dispense = (floraBloom_tea_per_gal * tea_spoon_ml * liquid)
        floraMicro_dispense = (floraMicro_tea_per_gal * tea_spoon_ml * liquid)
        # dispense tiger bloom
        pump(FLORAGROW_PIN, floraGrow_dispense)
        # dispense big bloom
        pump(FLORABLOOM_PIN, floraBloom_dispense)
        # dispense big grow
        pump(FLORAMICRO_PIN, floraMicro_dispense)
        # log amount dispensed
        record_nutrient_log(active_grow, floraGrow_dispense, floraBloom_dispense, floraMicro_dispense)