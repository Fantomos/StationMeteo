#IMPORTS
from config import ConfigFile
from gsm import Gsm
from pic import I2C, Pic
from loguru import logger
from sensors import Sensors
from sigfox import Sigfox
from radio import Radio
import RPi.GPIO as GPIO
from os import system

def setRpiTime(dt):
    if len(dt) == 6:
        os.system('sudo date --set="' + str(dt[0]) + "-" + str(dt[1]) + "-" + str(dt[2]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]) + '.000"')



MESURES_TRY = 5
NB_MESURES = 1
CONFIG_FILENAME = "config.txt"
PIC_ADDR = 0x21

SIGFOX_ADDR = 0x55
SIGFOX_MESS_LENGTH = 12

TTS_SPEED = 120
TTS_PITCH = 30

GPIO_GSM_POWER = 
GPIO_DHT11 = 23
GPIO_TW = 29
GPIO_PTT = 31
GPIO_EXTINCTION = 


# Configuration des loggers (log, data et batterie)
logger.add("logs.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("data.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("battery.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")
logger_log = logger.bind(type="LOG")
logger_data = logger.bind(type="DATA")
logger_battery = logger.bind(type="BATTERY")

# Initialisation du fichier de configuration
config = ConfigFile(filename = CONFIG_FILENAME)

#Initialisation du bus I2C, PIC, Sensors, GSM, Sigfox et radio
i2c_bus = I2C(logger = logger_log, mesures_nbtry = MESURES_TRY)
pic = Pic(i2c_bus = i2c_bus, logger = logger_log,  i2c_address = PIC_ADDR)
gsm = Gsm(gsm_power_gpio=GPIO_GSM_POWER, pic = pic, config = config, logger = logger_log)
sensors = Sensors(dht11_gpio = GPIO_DHT11, pic = pic, config = config, logger = logger_log, logger_data=logger_data, mesures_nbtry=MESURES_TRY, nbmesures=NB_MESURES)
sigfox = Sigfox(i2c_bus=i2c_bus, i2c_address=SIGFOX_ADDR, logger=logger_log, message_length=SIGFOX_MESS_LENGTH)
radio = Radio(config = config, logger = logger_log,  speed = TTS_SPEED, pitch = TTS_PITCH, tw_gpio = GPIO_TW, ptt_gpio = GPIO_PTT)

#Initialisation GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_EXTINCTION, GPIO.IN)

#On récupère date et heure du GSM si possible, sinon on recupère sur le PIC
dateTime = gsm.getDateTime() 
if len(dateTime) == 6:
    pic.setDateTime(dateTime)
    setRpiTime(dateTime)
else:
    dateTime = pic.getDateTime()
    setRpiTime(dateTime)

#Recupère toutes les données des capteurs
sensorsData = sensors.getSensorsData()

#Joue le message audio sur la radio
radio.playVoiceMessage(sensorsData)

# Enregistre la tension de la batterie
logger_battery.info(sensorsData['Voltage'])

# Envoie les données via Sigfox
sigfox.sendData(sensorsData)

# Envoie les données via SMS
gsm.respondToSMS(sensorsData)
gsm.turnOff() #On éteint le module GSM
        
#On arrête le programme
pic.writePicReg("state", 2) # On annonce au PIC que le raspberry à fini

mixer.quit()



#Setup tout ce qui est nécessiare
def setup():
    
   # getAndUpdateConfig() #On vérifie que les fichiers de configuration sont présents
      
    # GSM setup
  

    gsm = initGSM()
    gsm.turnOn() #On allume le module GSM
    gsm.enterPIN() #On entre le code PIN
    gsm.setupSMS() #On setup les SMS
    
    # Sensors setup
    thermometre = initThermometer(n_try_connection)
    barometre = initBarometer(n_try_connection)
    busI2C = initI2C(n_try_connection)
    hygrometer = initHygrometer(n_try_connection)
    
    # Speech synthesis setup
    voice = initSpeechSynthesis()
    
    
    # Setup logger
    logger.add("logs.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}")
    
  

    #On setup les ports I/O du TW
    io.setmode(io.BOARD)
    io.setup(io_cmd_tw, io.OUT)
    io.setup(io_ptt, io.OUT)
    io.setup(io_extinction, io.IN)


#Méthode qui éteint tout
def extinction():
    pic.ecriture(pic_state, 2) #On annonce au PIC qu'il peut s'endormir
    gsm.turnOff() #On éteint le module GSM
    mixer.quit()
    if io.input(io_extinction) == 1: #Si on est en mode cycle
        io.cleanup() #On libère le GPIO
        os.system("sudo shutdown -h now") #On éteint la Rpi
    else:
        io.cleanup() #On libère le GPIO
    

#######################
# PROGRAMME PRINCIPAL #
#######################

#Setup des différents modules
setup()

pic.resetWatchdogTimer() #Evite le WDT du PIC

#Lecture des capteurs et du PIC
temperature, humidite, pression, altitude, hauteur_nuages, direction_vent, vitesse_vent, direction_vent_moy, direction_vent_max, vitesse_vent_moy, vitesse_vent_max = sensors.getSensorsData()
heure_mesures = time.strftime("%Hh%M")

pic.resetWatchdogTimer()  #Evite le WDT du PIC
logger.info("Température : ", round(temperature, 1), " °C --- Humidité : ", round(humidite), " % --- Pression : ", pression, " hPa")
logger.info("Direction du vent : ", direction_vent, ' --- Vitesse du vent : ', vitesse_vent, ' km/h')
    
#On joue le message radio
playVoiceMessage()

#Enregistrement de la tension de la batterie
tension_batterie = pic.lecture(pic_batterie) / 10
sensors.saveBatteryValues(tension_batterie)

#On envoie les données par Sigfox
sigfox.sendValuesToSigFox(temperature, humidite, pression, vitesse_vent, direction_vent, tension_batterie, True)
logger.info("Envoyé !")

#Envoie l'heure au PIC (et la récupère dans la variable dateTime)
dateTime = gsm.getDateTime() #On récupère date et heure du GSM
pic.setDateTime(dateTime)
setRpiTime(dateTime)

if len(dateTime) == 6:
    heure_mesures = str(dateTime[3]) + ":" + str(dateTime[4])

#Lis et répond à tous les SMS en attente
respondToSMS(temperature, humidite, pression, altitude, hauteur_nuages, direction_vent, vitesse_vent, direction_vent_moy, direction_vent_max, vitesse_vent_moy, vitesse_vent_max, heure_mesures)


#Met la Raspberry Pi à l'heure

