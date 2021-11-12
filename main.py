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
MKRFOX_ADDR = 0x33
ATTINY_ADDR = 0x44
SIGFOX_ADDR = 0x55
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

logger_log.info("#################################################################")
logger_log.info("###################### DEBUT NOUVEAU CYCLE ######################")
logger_log.info("#################################################################")

# Initialisation du fichier de configuration
config = ConfigFile(filename = CONFIG_FILENAME)

# Initialise l'instancie pigpio
pi = pigpio.pi()

#Initialisation du bus I2C, PIC, Sensors, GSM, Sigfox et radio
mkrfox = Mkrfox(pi = pi, i2c_address = MKRFOX_ADDR, logger = logger_log, nb_try=MESURES_TRY)
attiny = Attiny(pi = pi, i2c_address = ATTINY_ADDR, logger = logger_log, nb_try=MESURES_TRY)
gsm = Gsm(gsm_power_gpio=GPIO_GSM_POWER, config = config, logger = logger_log, mesures_nbtry=MESURES_TRY)
sensors = Sensors(dht11_gpio = GPIO_DHT11, config = config, logger = logger_log, logger_data=logger_data, mesures_nbtry=MESURES_TRY, nbmesures=NB_MESURES)
radio = Radio(config = config, logger = logger_log,  speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)

# Initialisation GPIO
GPIO.setmode(GPIO.BOARD)

# On récupère date et heure du GSM si possible, sinon on recupère sur le PIC
epochTime = gsm.getDateTime() 
if epochTime != 0:
    mkrfox.write("time", epochTime, 4)
    system("sudo date -s '@" + int(epochTime) + "'")
else:
    logger_log.info("Tentative d'actualiser l'heure depuis le module SigFox...")
    mkrfox.write("time", 0, 1)
    sleep(1)
    epochTime = mkrfox.read("time", 4)
    if epochTime != 0:
        system("sudo date -s '@" + str(epochTime) + "'")
        logger_log.success("Date et heure actualisées depuis le module SigFox")
    else:
        logger_log.error("Impossible d'actualisées l'heure depuis le module SigFox")

# Recupère les données des capteurs connectées au Raspberry
sensorsData = sensors.getRPISensorsData()

# Récupère les données des capteurs connectées au ATTINY
windData = attiny.getWindData()

# Mise à jour des données
sensorsData.update(windData)

# Logs des données
logger_data.info(",".join([str(d) for d in sensorsData.items()]))

# Récupère la tension de la batterie et l'enregistre dans un log
logger_log.info("Lecture de la tension de la batterie...")
try:
    battery = mkrfox.read("battery", 4)/10
except:
    logger_log.error("Impossible de lire la tension de la batterie")
    battery = 0
else:
    logger_log.success("Lecture terminée")
sensorsData["Battery"] = battery
logger_battery.info(sensorsData['Battery'])

# Joue le message audio sur la radio
radio.playVoiceMessage(sensorsData)

# Envoie les données via Sigfox
mkrfox.sendData(sensorsData)

# Envoie les données via SMS
gsm.respondToSMS(sensorsData)

#On éteint le module GSM
gsm.turnOff() 
        
#On nettoie les entrées/sorties
GPIO.cleanup()

# On signale au mkrfox que le cycle est terminé
mkrfox.write("state", 2, 4) 
logger_log.info("Cycle terminé ! Extinction du raspberry immédiate")
logger_log.info("\n\n")


# On éteint le Rpi
#system("sudo shutdown -h now") 


