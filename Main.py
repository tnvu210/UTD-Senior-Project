from controller import Controller
from controller import GardenDb
import sys
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')
import time
import schedule
import logging



# setup on boot
# create logger
logger = logging.getLogger('garden')
logger.setLevel(logging.DEBUG)
# create file handler
fh = logging.FileHandler('garden.log')
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
#add handlers to logger
logger.addHandler(fh)
logger.addHandler(ch)
logger.info('creating instance of controller.Controller')
controller = Controller.Controller()

schedule.clear()
#schedule.every(30).minutes.do(controller.adjust_ph).tag("ph")
schedule.every(10).minutes.do(controller.record_readings).tag("record")
schedule.every(15).minutes.do(controller.adjust_humidity).tag("humidity")
schedule.every(15).minutes.do(controller.adjust_temp).tag("temp")
schedule.every().hour.do(controller.get_active_grow).tag("update")
schedule.every().hour.do(controller.get_active_plants).tag("update")
schedule.every().hour.do(controller.get_lighting_type).tag("update")
#schedule.every().day.do(controller.adjust_nutrients).tag("nutrients")
lighting_times = controller.init_lights()
if lighting_times is not None:
    for lighting_time in lighting_times:
        if lighting_time.lighting:
            schedule.every().day.at(lighting_time.lighting_time).do(controller.lights_on).tag("lights")
        else:
            schedule.every().day.at(lighting_time.lighting_time).do(controller.lights_off).tag("lights")


# run forever
while True:
    while controller.active_grow is not None:
        # make any updates to scheduling or conditions if needed
        if controller.change_light_times:
            lighting_times = controller.init_lights()
            if lighting_times is not None:
                for lighting_time in lighting_times:
                    if lighting_time.lighting:
                        schedule.every().day.at(lighting_time.lighting_time).do(controller.lights_on).tag("lights")
                    else:
                        schedule.every().day.at(lighting_time.lighting_time).do(controller.lights_off).tag("lights")

            controller.change_light_times = False

        schedule.run_pending()
        #time.sleep(1)

    logger.info('No active grow. Sleeping for 5 minutes')
    time.sleep(60 * 5)
    controller.get_active_grow()