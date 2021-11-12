#IMPORTS
from time import sleep
from attiny import Attiny
from config import ConfigFile
from gsm import Gsm
from mkrfox import Mkrfox
from i2c import I2C
from loguru import logger
from sensors import Sensors
from radio import Radio
from attiny import Attiny
import RPi.GPIO as GPIO
from smbus2 import SMBus
from os import system

MESURES_TRY = 5
NB_MESURES = 3
CONFIG_FILENAME = "config.ini"
MKRFOX_ADDR = 0x55
ATTINY_ADDR = 0x44
SIGFOX_MESS_LENGTH = 12

TTS_SPEED = 120
TTS_PITCH = 30

GPIO_GSM_POWER = 1
GPIO_DHT11 = 23
GPIO_TW = 29
GPIO_PTT = 31


# Configuration des loggers (log, data et batterie)
logger.add("logs/logs.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("logs/data.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("logs/battery.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")
logger_log = logger.bind(type="LOG")
logger_data = logger.bind(type="DATA")
logger_battery = logger.bind(type="BATTERY")


i2c_bus = I2C(logger = logger_log, mesures_nbtry = MESURES_TRY)

res = i2c_bus.readReg(0x55,0x04,1)
print(res)