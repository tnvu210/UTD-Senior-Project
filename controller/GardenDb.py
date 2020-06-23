import sys
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')
import pymysql
import datetime
from peewee import *
from playhouse.pool import PooledMySQLDatabase

db = PooledMySQLDatabase('garden',
                         max_connections=32,
                         stale_timeout=300,
                         host='localhost',
                         user='garden',
                         passwd='controllerpi')


class BaseModel(Model):
    """A base model that will use our MySQL database"""

    class Meta:
        database = db


class LightingType(BaseModel):
    lighting_type_id = PrimaryKeyField()
    lighting_type = CharField()


    class Meta:
        db_table = 'LightingType'


class LightingTimes(BaseModel):
    lighting_times_id = PrimaryKeyField()
    lighting_type_id = ForeignKeyField(LightingType, db_column='lighting_type_id')
    lighting = BooleanField()
    lighting_time = CharField()

    class Meta:
        db_table = 'LightingTimes'

class Plants(BaseModel):
    plant_id = PrimaryKeyField()
    plant_name = CharField()
    humidity_max = FloatField()
    temp_min = FloatField()
    temp_max = FloatField()
    ph_target = FloatField()
    seedling_days = SmallIntegerField()
    vege_days = SmallIntegerField()
    flower_days = SmallIntegerField()

    class Meta:
        db_table = 'Plants'


class Stage(BaseModel):
    stage_id = PrimaryKeyField()
    stage = CharField()

    class Meta:
        db_table = 'Stage'


class Grow(BaseModel):
    grow_id = PrimaryKeyField()
    start_date = DateField(default=datetime.date.today())
    end_date = DateField()
    is_active = BooleanField()
    lighting_type_id = ForeignKeyField(LightingType, db_column='lighting_type_id')
    stage_id = ForeignKeyField(Stage, db_column='stage_id')

    class Meta:
        db_table = 'Grow'


class GrowLog(BaseModel):
    log_id = PrimaryKeyField()
    reading_time = DateTimeField(default=datetime.datetime.now())
    temp = FloatField()
    humidity = FloatField()
    ph = FloatField()
    ec = FloatField()
    gallons = FloatField()
    grow_id = ForeignKeyField(Grow, db_column='grow_id')

    class Meta:
        db_table = 'GrowLog'


class Plants_Grow(BaseModel):
    plants_grow_id = PrimaryKeyField()
    grow_id = ForeignKeyField(Grow, db_column='grow_id')
    plant_id = ForeignKeyField(Plants, db_column='plant_id')

    class Meta:
        db_table = 'Plants_Grow'


class PumpLog(BaseModel):
    pump_log_id = PrimaryKeyField()
    grow_id = ForeignKeyField(Grow, db_column='grow_id')
    dispense_time = DateTimeField(default=datetime.datetime.now())
    ph_up_ml = FloatField()
    ph_down_ml = FloatField()
    tiger_bloom_ml = FloatField()
    big_bloom_ml = FloatField()
    grow_ml = FloatField()

    class Meta:
        db_table = 'PumpLog'


class FeedingLog(BaseModel):
    feeding_log_id = PrimaryKeyField()
    pump_log_id = ForeignKeyField(PumpLog, db_column='pump_log_id')
    record = DateField(default=datetime.date.today())

    class Meta:
        db_table = 'FeedingLog'


class Flags(BaseModel):
    flag_id = PrimaryKeyField()
    flag_name = CharField()
    flag = BooleanField()
    last_changed = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = 'Flags'