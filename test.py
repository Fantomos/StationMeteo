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

MESURES_TRY = 1
NB_MESURES = 1
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
# gsm = Gsm(gsm_power_gpio=GPIO_GSM_POWER, config = config, logger = logger_log, mesures_nbtry=MESURES_TRY)
sensors = Sensors(dht11_gpio = GPIO_DHT11, config = config, logger = logger_log, logger_data=logger_data, mesures_nbtry=MESURES_TRY, nbmesures=NB_MESURES)
radio = Radio(config = config, logger = logger_log,  speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)

# Initialisation GPIO
GPIO.setmode(GPIO.BOARD)





# Recupère les données des capteurs connectées au Raspberry
sensorsData = sensors.getRPISensorsData()
#  print(sensorsData)
sensorsData.update({"Direction":0, "Speed":0, "Direction_max":0, "Speed_max":0, "Battery":0})

# Joue le message audio sur la radio
radio.playVoiceMessage(sensorsData)

mkrfox.sendData(sensorsData)
# attiny.askRead()
# sleep(2)
# print(attiny.read(14))

# On signale au mkrfox que le cycle est terminé
# mkrfox.write("wakeup", 45)
# print(mkrfox.read("wakeup"))
# print(mkrfox.read("battery"))     

pi.stop()
GPIO.cleanup()
logger_log.info("#################################################################")
logger_log.info("########################### FIN CYCLE ###########################")
logger_log.info("#################################################################")


# On éteint le Rpi
#system("sudo shutdown -h now") 


