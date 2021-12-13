
## @file main.py
# Script principal du Raspberry Pi. Il est automatiquement exécuté au démarrage à l'aide d'un service.
##

from time import sleep
from attiny import Attiny
from config import ConfigFile
from gsm import Gsm
from mkrfox import Mkrfox
from loguru import logger
from sensors import Sensors
from radio import Radio
from attiny import Attiny
from os import system
import time
import pigpio

## Nombre d'essais pour l'initialisation des capteurs
MESURES_TRY = 3
## Nombre de mesures des capteurs
NB_MESURES = 1 
## Nom du fichier de configuration
CONFIG_FILENAME = "config.ini" 
## Addresse I2C du MKRFOX
MKRFOX_ADDR = 0x55 
## Addresse I2C du ATTINY
ATTINY_ADDR = 0x44 

## Vitesse de lecture de la synthèse vocale
TTS_SPEED = 120 
## Tonalité de la synthèse vocale
TTS_PITCH = 30 

## Numéro de pin du capteur d'humidité DHT11
GPIO_DHT11 = 23
## Numéro de pin du transistor contrôlant l'alimentation du talkie-walkie
GPIO_TW = 5
## Numéro de pin du relais contrôlant le push-to-talk
GPIO_PTT = 6



# Configuration des loggers (log, data et batterie)
logger.add("logs/logs.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("logs/data.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("logs/battery.txt", rotation="1 days", retention=30, level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")
## Logger des logs généraux
logger_log = logger.bind(type="LOG")
## Logger des bulletins météo
logger_data = logger.bind(type="DATA")
## Logger des tension de la batterie
logger_battery = logger.bind(type="BATTERY")

logger_log.info("#################################################################")
logger_log.info("###################### DEBUT NOUVEAU CYCLE ######################")
logger_log.info("#################################################################")

## Initialisation du fichier de configuration
config = ConfigFile(filename = CONFIG_FILENAME)

## Initialise l'instancie pigpio
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

## Initialisation de l'instance Mkrfox
mkrfox = Mkrfox(pi = pi, i2c_address = MKRFOX_ADDR, logger = logger_log, nb_try=MESURES_TRY)
## Initialisation de l'instance Attiny
attiny = Attiny(pi = pi, i2c_address = ATTINY_ADDR, logger = logger_log, nb_try=MESURES_TRY)
## Initialisation de l'instance Sensors
sensors = Sensors(dht11_gpio = GPIO_DHT11, config = config, logger = logger_log, logger_data=logger_data, init_nbtry=MESURES_TRY, nb_mesures=NB_MESURES)
## Initialisation de l'instance Radio
radio = Radio(config = config, logger = logger_log, pi = pi, speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)
## Initialisation de l'instance GSM
gsm = Gsm(config = config, logger = logger_log, mesures_nbtry=MESURES_TRY)

## Registre d'état du cycle
state = mkrfox.read("state")
mkrfox.write("state",state | 0b00000001)


# Si c'est le premier cycle de la journée alors on récupère date et heure du GSM si possible, sinon on recupère sur le MKRFOX
if(state & 0b00000100 == 4):
    gsm.setup()
    ## Temps actuel au format epoch
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
else:
    epochTime = mkrfox.read("time")
    if epochTime != 0: # Si l'heure est différente de 0 on met à jour l'heure système du Raspberry, sinon erreur
        system("sudo date -s '@" + str(epochTime) + "'")
        logger_log.success("Date et heure actualisées depuis le MKRFOX")
    else:
        logger_log.error("Impossible d'actualisées l'heure depuis le MKRFOX")
    

if time.localtime().tm_hour > config.getSleepHour() or time.localtime().tm_hour < config.getWakeupHour():
    mkrfox.write("state", 0) 
    logger_log.info("Heure actuelle en dehors de la plage fonctionnement. Extinction du raspberry immédiate")
    logger_log.info("#################################################################")
    logger_log.info("########################### FIN CYCLE ###########################")
    logger_log.info("#################################################################")
    logger_log.info("\n\n")
    # system("sudo shutdown -h now") 
    exit()

## Requête des données du vent
attiny.askRead()

## Recupère les données des capteurs connectées au Raspberry
sensorsData = sensors.getRPISensorsData()

## Récupère les données des capteurs connectées au ATTINY
windData = attiny.getWindData()

# Mise à jour des données
sensorsData.update(windData)

# Logs des données
logger_data.info(",".join([str(d) for d in sensorsData.items()]))

# Récupère la tension de la batterie et l'enregistre dans un log
logger_log.info("Lecture de la tension de la batterie...")
try:
    battery = mkrfox.read("battery")
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

## Met à jour la configuration sur le MKRFOX
configData = {"sleep":config.getSleepHour(),"wakeup":config.getWakeupHour(),"battery_threshold":config.getBatteryLimit()}
mkrfox.updateConfig(configData)

# On signale au mkrfox que le cycle est terminé
mkrfox.write("state", 0) 
logger_log.info("Extinction du raspberry immédiate")
logger_log.info("#################################################################")
logger_log.info("########################### FIN CYCLE ###########################")
logger_log.info("#################################################################")
logger_log.info("\n\n")

#On nettoie les entrées/sorties
pi.stop()

# On éteint le Rpi
#system("sudo shutdown -h now") 


