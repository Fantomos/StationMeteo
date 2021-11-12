#IMPORTS
from time import sleep
from attiny import Attiny
from config import ConfigFile
from gsm import Gsm
from mkrfox import Mkrfox
from loguru import logger
from sensors import Sensors
from radio import Radio
from attiny import Attiny
import RPi.GPIO as GPIO
from os import system
import pigpio

MESURES_TRY = 5
NB_MESURES = 3
CONFIG_FILENAME = "config.ini"
MKRFOX_ADDR = 0x55
ATTINY_ADDR = 0x44


TTS_SPEED = 120
TTS_PITCH = 30

GPIO_GSM_POWER = 1
GPIO_DHT11 = 23
GPIO_TW = 29
GPIO_PTT = 31


# Configuration des loggers (log, data et batterie)
logger.add("logs/logs.txt", rotation="1 days", retention=7, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("logs/data.txt", rotation="1 days", retention=7, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("logs/battery.txt", rotation="1 days", retention=7, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")
logger_log = logger.bind(type="LOG")
logger_data = logger.bind(type="DATA")
logger_battery = logger.bind(type="BATTERY")

logger_log.info("#################################################################")
logger_log.info("###################### DEBUT NOUVEAU CYCLE ######################")
logger_log.info("#################################################################")

# Initialisation du fichier de configuration
config = ConfigFile(filename = CONFIG_FILENAME)

# Initialise l'instancie pigpio
pi = pigpio.pi()
if not pi.connected:
    logger_log.info("Lancement du deamon pigpiod")
    system("sudo pigpiod") 
    pi = pigpio.pi()
    if not pi.connected:
        logger_log.error("Impossible d'initialiser pigpio.")
        exit()
    else:
        logger_log.success("Pigpio initialisé")
else:
    logger_log.success("Pigpio initialisé")

#Initialisation du bus I2C, PIC, Sensors, GSM, Sigfox et radio
mkrfox = Mkrfox(pi = pi, i2c_address = MKRFOX_ADDR, logger = logger_log, nb_try=MESURES_TRY)
attiny = Attiny(pi = pi, i2c_address = ATTINY_ADDR, logger = logger_log, nb_try=MESURES_TRY)


# On signale au mkrfox que le cycle est terminé
mkrfox.write("wakeup", 45)
print(mkrfox.read("wakeup"))
        

pi.stop()

logger_log.info("#################################################################")
logger_log.info("########################### FIN CYCLE ###########################")
logger_log.info("#################################################################")


# On éteint le Rpi
#system("sudo shutdown -h now") 


