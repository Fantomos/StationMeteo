#IMPORTS
from time import sleep
from config import ConfigFile
from gsm import Gsm
from mkrfox import Mkrfox
from i2c import I2C
from loguru import logger
from sensors import Sensors
from sigfox import Sigfox
from radio import Radio
import RPi.GPIO as GPIO
from os import system

MESURES_TRY = 5
NB_MESURES = 1
CONFIG_FILENAME = "config.txt"
MKRFOX_ADDR = 0x21

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

# Initialisation du fichier de configuration
config = ConfigFile(filename = CONFIG_FILENAME)

#Initialisation du bus I2C, PIC, Sensors, GSM, Sigfox et radio
i2c_bus = I2C(logger = logger_log, mesures_nbtry = MESURES_TRY)
mkrfox = Mkrfox(i2c_bus = i2c_bus, logger = logger_log,  i2c_address = MKRFOX_ADDR)
gsm = Gsm(gsm_power_gpio=GPIO_GSM_POWER, pic = pic, config = config, logger = logger_log)
sensors = Sensors(dht11_gpio = GPIO_DHT11, pic = pic, config = config, logger = logger_log, logger_data=logger_data, mesures_nbtry=MESURES_TRY, nbmesures=NB_MESURES)
sigfox = Sigfox(i2c_bus=i2c_bus, i2c_address=SIGFOX_ADDR, logger=logger_log, message_length=SIGFOX_MESS_LENGTH)
radio = Radio(config = config, logger = logger_log,  speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)

# Initialisation GPIO
GPIO.setmode(GPIO.BOARD)

# On récupère date et heure du GSM si possible, sinon on recupère sur le PIC
epochTime = gsm.getDateTime() 
if epochTime != 0:
    mkrfox.write("time", epochTime, 4)
    system("sudo date -s '@" + int(epochTime) + "'")
    logger_log.info("Date et heure actualisées depuis le module GSM")
else:
    mkrfox.write("time", 0, 1)
    sleep(1000)
    epochTime = mkrfox.read("time", 4)
    system("sudo date -s '@" + int(epochTime) + "'")
    logger_log.info("Date et heure actualisées depuis le module SigFox")

# Recupère les données des capteurs connectées au Raspberry
sensorsData = sensors.getRPISensorsData()

# Récupère les données des capteurs connectées au ATTINY
windData = 0
# {"Direction":wind_data[0], "Speed":wind_data[1], "Direction_max":wind_data[2], "Speed_max":wind_data[3], "Voltage":battery_voltage}
sensorsData.update(windData)

# Récupère la tension de la batterie et l'enregistre dans un log
battery = mkrfox.read("battery", 4)/10
sensorsData["Battery"] = battery
logger_battery.info(sensorsData['Voltage'])

# Joue le message audio sur la radio
radio.playVoiceMessage(sensorsData)

# Envoie les données via Sigfox
sigfox.sendData(sensorsData)

# Envoie les données via SMS
gsm.respondToSMS(sensorsData)
gsm.turnOff() #On éteint le module GSM
        
#On arrête le programme
mixer.quit()
io.cleanup()
mkrfox.write("state", 2) 
system("sudo shutdown -h now") #On éteint la Rpi


