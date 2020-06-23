from controller import GardenDb
from controller import water_system
from controller import environment_system
from controller import Singleton
import sys
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')
import wiringpi
from datetime import datetime, time
import logging
import peewee


class Controller():
    """Interface for scheduling system functions"""

    def __init__(self):
        wiringpi.wiringPiSetup()
        #init all pins
        wiringpi.pinMode(water_system.FLORAGROW_PIN, 1)
        wiringpi.pinMode(water_system.FLORABLOOM_PIN, 1)
        wiringpi.pinMode(water_system.FLORAMICRO_PIN, 1)
        wiringpi.pinMode(water_system.PH_UP_PIN, 1)
        wiringpi.pinMode(water_system.PH_DOWN_PIN, 1)
        wiringpi.pinMode(environment_system.FAN_PIN, 1)
        wiringpi.pinMode(environment_system.LED_PIN, 1)
        wiringpi.pinMode(environment_system.DEHUMIDIFIER_PIN, 1)
        #ensuer all relays are off
        wiringpi.digitalWrite(environment_system.DEHUMIDIFIER_PIN, 1)
        wiringpi.digitalWrite(environment_system.FAN_PIN, 1)
        wiringpi.digitalWrite(water_system.FLORAGROW_PIN, 1)
        wiringpi.digitalWrite(water_system.FLORABLOOM_PIN, 1)
        wiringpi.digitalWrite(water_system.FLORAMICRO_PIN, 1)
        wiringpi.digitalWrite(water_system.PH_DOWN_PIN, 1)
        wiringpi.digitalWrite(water_system.PH_UP_PIN, 1)
        # create this objects attributes
        self.logger = logging.getLogger('garden.controller.Controller')
        self.logger.info('creating instance of controller.Controller')
        self.active_grow = None
        self.active_plants = None
        self.lighting_type = None
        self.change_light_times = False
        self.get_active_plants()
        self.get_active_grow()
        self.get_lighting_type()
        self.led = False
        self.fan = False
        self.dehumidifier = False

    def get_active_plants(self):
        """Update plant attribute and check if attribute has changed"""
        if self.active_plants is not None:
            temp = self.active_plants
        else:
            temp = None

        GardenDb.db.get_conn()
        self.active_plants = (GardenDb.Plants.select()
                              .join(GardenDb.Plants_Grow)
                              .join(GardenDb.Grow)
                              .where(GardenDb.Grow.is_active == 1)).first()
        GardenDb.db.close()
        self.logger.info('active plants just updated from db')
        if temp is not None:
            self.logger.info('check if any conditions have changed - not implemented yet')
            pass
        return self.active_plants

    def get_active_grow(self):
        GardenDb.db.get_conn()
        self.active_grow = (GardenDb.Grow.select()
                            .where(GardenDb.Grow.is_active == 1)).first()
        GardenDb.db.close()
        self.logger.info('active grow just updated from db')
        return self.active_grow

    def get_lighting_type(self):
        if self.lighting_type is not None:
            temp = self.lighting_type
        else:
            temp = None
        GardenDb.db.get_conn()
        self.lighting_type = GardenDb.LightingType.select().where(GardenDb.LightingType.lighting_type_id == self.active_grow.lighting_type_id).first()
        GardenDb.db.close()
        self.logger.info('lighting type updated from db')
        if temp is not None:
            self.logger.info('check if lighs have changed')
            if temp.lighting_type_id != self.lighting_type.lighting_type_id:
                self.change_light_times = True

        return self.lighting_type

    def record_readings(self):
        """read all sensors and write values to the db"""
        GardenDb.db.get_conn()
        ph_reading = water_system.ph()
        ec_reading = water_system.ec()
        humidity_temp = environment_system.humidity_temp()
        gallons_reading = water_system.gallons()
        q = GardenDb.GrowLog.insert(reading_time=datetime.now(), temp=humidity_temp[2],
                                    humidity=humidity_temp[0], ph=ph_reading, ec=ec_reading,
                                    gallons=gallons_reading, grow_id=self.active_grow)
        q.execute()
        GardenDb.db.close()
        self.logger.info('readings recorded to db')

    def pump_ph(self, pin, amount):
        if pin:
            water_system.pump(water_system.PH_UP_PIN, amount)
        else:
            water_system.pump(water_system.PH_DOWN_PIN, amount)

    def adjust_ph(self):
        self.logger.info('calling water_system.dispense_ph()')
        ideal_ph = self.active_plants.ph_target
        water_system.dispense_ph(ideal_ph, self.active_grow)
        self.logger.info('finished water_system.dispense_ph()')

    def adjust_humidity(self):
        self.logger.info('checking current humdidity against ideal')
        ideal_humidity = self.active_plants.humidity_max
        reading = environment_system.humidity_temp()
        if self.dehumidifier:
            #if dehumidifer is on turn off when humidity less than ideal
            if reading[0] < ideal_humidity:
                environment_system.dehumidifier_off()
                self.dehumidifier = False
        else:
            #if dehumidifier is off turn on when humidity is more than ideal
            if reading[0] > ideal_humidity:
                environment_system.dehumidifier_on()
                self.dehumidifier = True

    def adjust_temp(self):
        self.logger.info('checking current temp agasint ideal')
        max_temp = self.active_plants.temp_max
        reading = environment_system.humidity_temp()
        if self.fan:
            #if fan is on turn off when temp is below max
            if reading[2] < max_temp:
                environment_system.fan_off()
                self.fan = False
        else:
            #if fan is off turn on when temp is above max
            if reading[2] > max_temp:
                environment_system.fan_on()
                self.fan = True

    def adjust_nutrients(self):
        self.logger.info('calling water_system.dispense_ph()')
        ideal_ec = 0.3283143
        water_system.pump_nutrients_adjust(ideal_ec, self.active_grow)
        self.logger.info('finished water_system.dispense_ph()')

    def full_feeding(self):
        water_system.pump_nutrients_full_feeding(self.active_grow)

    def lights_on(self):
        self.logger.info('calling environment_system.lights_on()')
        environment_system.lights_on()
        self.led = True
        self.logger.info('finished environment_system.lights_on()')

    def lights_off(self):
        self.logger.info('calling environment_system.lights_off()')
        environment_system.lights_off()
        self.led = False
        self.logger.info('finished environment_system.lights_off()')

    def init_lights(self):
        """Turns lights on if they should be, returns times"""

        if self.lighting_type.lighting_type == '12-12':  # 12-12 lights 10am-10pm default
            now = datetime.now()
            time_on = []
            time_off = []
            light_times = GardenDb.LightingTimes.select().where(
                GardenDb.LightingTimes.lighting_type_id == self.lighting_type.lighting_type_id)
            for light_time in light_times:
                if light_time.lighting:
                    time_on = light_time.split(':')
                else:
                    time_off = light_time.split(':')

            if time(int(time_on[0]),int(time_on[1])) <= now.time() <= time(int(time_off[0]),int(time_off[1])):
                self.logger.info('turning lights on during init (daytime)')
                self.lights_on()
            else:
                self.logger.info('keeping lights off during init (nighttime)')
                self.lights_off()

            return light_times

        elif self.lighting_type.lighting_type == '24 hour':  # 24 hour on
            self.logger.info('turning lights on (24 hour)')
            self.lights_on()
            return None

        elif self.lighting_type.lighting_type == "6-2": #6 on 2 off
            now = datetime.now()
            light_times = GardenDb.LightingTimes.select().where(
                GardenDb.LightingTimes.lighting_type_id == self.lighting_type.lighting_type_id)
            time_on = []
            time_off =[]
            for light_time in light_times:
                if light_time.lighting:
                    temp = light_time.lighting_time.split(':')
                    time_on.append(temp[0])
                    time_on.append(temp[1])
                else:
                    temp = light_time.lighting_time.split(':')
                    time_off.append(temp[0])
                    time_off.append(temp[1])

            if time(int(time_on[0]),int(time_on[1])) <= now.time() <= time(int(time_off[0]),int(time_off[1])):
                self.lights_on()
            elif time(int(time_on[2]),int(time_on[3])) <= now.time() <= time(int(time_off[2]),int(time_off[3])):
                self.lights_on()
            elif time(int(time_on[4]),int(time_on[5])) <= now.time() <= time(int(time_off[4]),int(time_off[5])):
                self.lights_on()
            else:
                self.lights_off()

            return light_times