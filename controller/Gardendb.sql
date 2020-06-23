DROP DATABASE IF EXISTS garden;
CREATE DATABASE garden;
USE garden;
CREATE TABLE LightingType (
    lighting_type_id int NOT NULL AUTO_INCREMENT,
    lighting_type VARCHAR(255) NOT NULL,
    PRIMARY KEY(lighting_type_id)
);
CREATE TABLE LightingTimes (
    lighting_times_id int NOT NULL AUTO_INCREMENT,
    lighting_type_id int,
    lighting BOOL,
    lighting_time VARCHAR(5),
    PRIMARY KEY(lighting_times_id),
    FOREIGN KEY (lighting_type_id) REFERENCES LightingType(lighting_type_id)
);
CREATE TABLE Plants (
	plant_id int NOT NULL AUTO_INCREMENT,
	plant_name varchar(255) NOT NULL,
	humidity_max float NOT NULL,
	temp_min float NOT NULL,
	temp_max float NOT NULL,
	ph_target float NOT NULL,
	seedling_days int NOT NULL,
	vege_days int NOT NULL,
	flower_days int NOT NULL,
	PRIMARY KEY (plant_id)
);
CREATE TABLE Stage (
    stage_id int NOT NULL AUTO_INCREMENT,
    stage varchar(255),
    PRIMARY KEY(stage_id)
);
CREATE TABLE Grow (
	grow_id int NOT NULL AUTO_INCREMENT,
	start_date DATE NOT NULL,
	end_date DATE,
	stage_id int,
	lighting_type_id int NOT NULL,
	is_active BOOL,
	PRIMARY KEY (grow_id),
	FOREIGN KEY (stage_id) REFERENCES Stage(stage_id),
	FOREIGN KEY (lighting_type_id) REFERENCES LightingType(lighting_type_id)
);
CREATE TABLE Plants_Grow (
	plants_grow_id int NOT NULL AUTO_INCREMENT,
	grow_id int NOT NULL,
	plant_id int NOT NULL,
	PRIMARY KEY (plants_grow_id),
	FOREIGN KEY (grow_id) REFERENCES Grow(grow_id),
	FOREIGN KEY (plant_id) REFERENCES Plants(plant_id)
);
CREATE TABLE GrowLog (
	log_id int NOT NULL AUTO_INCREMENT,
	reading_time DATETIME NOT NULL,
	temp float NOT NULL,
	humidity float NOT NULL,
	ph float NOT NULL,
	ec float NOT NULL,
	gallons float NOT NULL,
	grow_id int NOT NULL,
	PRIMARY KEY (log_id),
	FOREIGN KEY (grow_id) REFERENCES Grow(grow_id)
);
CREATE TABLE PumpLog (
    pump_log_id int NOT NULL AUTO_INCREMENT,
    grow_id int NOT NULL,
    dispense_time DATETIME NOT NULL,
    ph_up_ml FLOAT,
    ph_down_ml FLOAT,
    tiger_bloom_ml FLOAT,
    big_bloom_ml FLOAT,
    grow_ml FLOAT,
    PRIMARY KEY (pump_log_id),
    FOREIGN KEY (grow_id) REFERENCES Grow(grow_id)
);

CREATE TABLE Flags (
    flag_id int NOT NULL AUTO_INCREMENT,
    flag_name VARCHAR(255) NOT NULL,
    flag BOOL NOT NULL,
    last_changed DATETIME NOT NULL,
    PRIMARY KEY (flag_id)
);


INSERT INTO LightingType (lighting_type)
VALUES ('12-12');
SET @lighting_12 = LAST_INSERT_ID();
INSERT INTO LightingType(lighting_type)
VALUES ('24 hour');
SET @lighting_24 = LAST_INSERT_ID();
INSERT INTO LightingType(lighting_type)
VALUES ('6-2') ;
SET @lighting_62 = LAST_INSERT_ID();
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_12, TRUE, '10:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_12, FALSE, '22:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, TRUE, '10:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, FALSE, '16:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, TRUE, '18:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, False, '00:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, TRUE, '2:00');
INSERT INTO LightingTimes (lighting_type_id, lighting, lighting_time)
VALUES (@lighting_62, FALSE, '8:00');
INSERT INTO Plants (plant_name, humidity_max, temp_min, temp_max, ph_target,seedling_days,vege_days,flower_days)
VALUES ('Lettuce', 50, 60, 75, 6.5, 17, 28, 0);
SET @plant_id = LAST_INSERT_ID();
INSERT INTO Stage (stage)
VALUES ('Seedling');
INSERT INTO Stage (stage)
VALUES ('Vegetative');
SET @stage_id = LAST_INSERT_ID();
INSERT INTO Stage (stage)
VALUES ('Flowering');
INSERT INTO Grow (start_date, is_Active, stage_id, lighting_type_id)
VALUES (CURRENT_DATE, TRUE, @stage_id, @lighting_62);
SET @grow_id = LAST_INSERT_ID();
INSERT INTO Plants_Grow (grow_id, plant_id)
VALUES (@grow_id, @plant_id);
INSERT INTO Flags (flag_name, flag, last_changed)
VALUES ('water low', FALSE, CURRENT_DATE);
