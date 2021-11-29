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
import time
import pigpio

MESURES_TRY = 3
NB_MESURES = 5
CONFIG_FILENAME = "config.ini"
MKRFOX_ADDR = 0x55
ATTINY_ADDR = 0x44


TTS_SPEED = 120
TTS_PITCH = 30

GPIO_GSM_POWER = 1
GPIO_DHT11 = 23
GPIO_TW = 5
GPIO_PTT = 6



# Configuration des loggers (log, data et batterie)
logger.add("logs/logs.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("logs/data.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("logs/battery.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")
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
if not pi.connected: # On vérifie que le deamon pigpiod est bien en cours d'exécution sinon on le démarre
    logger_log.info("Lancement du deamon pigpiod")
    system("sudo pigpiod") 
    pi = pigpio.pi()
    if not pi.connected: # On vérifie si cette fois-ci le deamon fonctionne sinon on arrête le programme
        logger_log.error("Impossible d'initialiser pigpio.")
        exit()
    else:
        logger_log.success("Pigpio initialisé")
else:
    logger_log.success("Pigpio initialisé")

#Initialisation du bus I2C, PIC, Sensors, GSM, Sigfox et radio
mkrfox = Mkrfox(pi = pi, i2c_address = MKRFOX_ADDR, logger = logger_log, nb_try=MESURES_TRY)
attiny = Attiny(pi = pi, i2c_address = ATTINY_ADDR, logger = logger_log, nb_try=MESURES_TRY)
gsm = Gsm(gsm_power_gpio=GPIO_GSM_POWER, config = config, logger = logger_log, mesures_nbtry=MESURES_TRY)
sensors = Sensors(dht11_gpio = GPIO_DHT11, config = config, logger = logger_log, logger_data=logger_data, mesures_nbtry=MESURES_TRY, nbmesures=NB_MESURES)
radio = Radio(config = config, logger = logger_log, pi = pi, speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)

mkrfox.write("state",1)

# Initialisation GPIO
GPIO.setmode(GPIO.BOARD)

# On récupère date et heure du GSM si possible, sinon on recupère sur le MKRFOX
epochTime = gsm.getDateTime() 
if epochTime != 0:
    mkrfox.write("time", epochTime)
    system("sudo date -s '@" + str(epochTime) + "'")
else:
    logger_log.info("Tentative d'actualiser l'heure depuis le module SigFox...")
    mkrfox.write("time", 0) # On envoie 0 au registre time du MKRFOX pour lui signaler de recupérer l'heure par le module Sigfox 
    state = mkrfox.read("state")
    while(state & 0b00000010 != 2): # On attends que l'heure soit actualisé par le MKRFOX
        state = mkrfox.read("state")
    epochTime = mkrfox.read("time") # On reçois l'heure du MKRFOX
    if epochTime != 0: # Si l'heure est différente de 0 on met à jour l'heure système du Raspberry, sinon erreur
        system("sudo date -s '@" + str(epochTime) + "'")
        logger_log.success("Date et heure actualisées depuis le module SigFox")
    else:
        logger_log.error("Impossible d'actualisées l'heure depuis le module SigFox")
    mkrfox.write("state", state & 0b11111101)
    

if time.localtime().tm_hour > config.getSleepHour() or time.localtime().tm_hour < config.getWakeupHour():
    mkrfox.write("state", 0) 
    logger_log.info("Heure actuelle en dehors de la plage fonctionnement. Extinction du raspberry immédiate")
    logger_log.info("#################################################################")
    logger_log.info("########################### FIN CYCLE ###########################")
    logger_log.info("#################################################################")
    logger_log.info("\n\n")
    # system("sudo shutdown -h now") 
    exit()


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
    battery = mkrfox.read("battery")/10
except:
    logger_log.error("Impossible de lire la tension de la batterie")
    battery = 0
else:
    logger_log.success("Lecture de la batterie terminée")
sensorsData["Battery"] = battery
logger_battery.info(sensorsData['Battery'])

# Joue le message audio sur la radio
radio.playVoiceMessage(sensorsData)

# Envoie les données au MKRFOX pour transmision via SigFox
mkrfox.sendData(sensorsData)

# Envoie les données via SMS
gsm.respondToSMS(sensorsData)

#On éteint le module GSM
gsm.turnOff() 
        
#On nettoie les entrées/sorties
GPIO.cleanup()
pi.stop()

# On signale au mkrfox que le cycle est terminé
mkrfox.write("state", 0) 
logger_log.info("Extinction du raspberry immédiate")
logger_log.info("#################################################################")
logger_log.info("########################### FIN CYCLE ###########################")
logger_log.info("#################################################################")
logger_log.info("\n\n")


# On éteint le Rpi
#system("sudo shutdown -h now") 


