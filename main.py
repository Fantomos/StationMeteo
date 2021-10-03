#IMPORTS
from gsm import *
import config

def setRpiTime(dt):
    if len(dt) == 6:
        os.system('sudo date --set="' + str(dt[0]) + "-" + str(dt[1]) + "-" + str(dt[2]) + " " + str(dt[3]) + ":" + str(dt[4]) + ":" + str(dt[5]) + '.000"')



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
logger_log.info("Température : ", round(temperature, 1), " °C --- Humidité : ", round(humidite), " % --- Pression : ", pression, " hPa")
logger_log.info("Direction du vent : ", direction_vent, ' --- Vitesse du vent : ', vitesse_vent, ' km/h')
    
#On joue le message radio
playVoiceMessage()

#Enregistrement de la tension de la batterie
tension_batterie = pic.lecture(pic_batterie) / 10
sensors.saveBatteryValues(tension_batterie)

#On envoie les données par Sigfox
sigfox.sendValuesToSigFox(temperature, humidite, pression, vitesse_vent, direction_vent, tension_batterie, True)
logger_log.info("Envoyé !")

#Envoie l'heure au PIC (et la récupère dans la variable dateTime)
dateTime = gsm.getDateTime() #On récupère date et heure du GSM
pic.setDateTime(dateTime)
setRpiTime(dateTime)

if len(dateTime) == 6:
    heure_mesures = str(dateTime[3]) + ":" + str(dateTime[4])

#Lis et répond à tous les SMS en attente
respondToSMS(temperature, humidite, pression, altitude, hauteur_nuages, direction_vent, vitesse_vent, direction_vent_moy, direction_vent_max, vitesse_vent_moy, vitesse_vent_max, heure_mesures)


#Met la Raspberry Pi à l'heure

#Envoie au PIC 0 pour l'alarme des minutes et 45 pour les secondes
pic.ecriture(pic_alm_min, pic_alm_min_val)
pic.ecriture(pic_alm_sec, pic_alm_sec_val)

#Récupère l'heure, soit sur le GSM, soit sur le PIC si il y a un problème avec le GSM
heure = int(dateTime[3]) if len(dateTime) == 6 else bcd2dec(pic.lecture(pic_hour))

#Si l'heure est après l'heure d'extinction, on modifie l'alarme pour l'heure de réveil
if heure >= int(config.getHeureSleep()):
    pic.ecriture(pic_alrmcon, pic_alrmcon_sleep) #On dit que l'alarme est maintenant quotidienne
    pic.ecriture(pic_alm_hour, dec2bcd(config.getHeureEveil())) #On dit que l'heure de réveil est celle enregistrée
    logger_log.info("Prochain reveil : demain")
else: #Sinon on redis toutes les 10 minutes
    pic.ecriture(pic_alrmcon, pic_alrmcon_eveil) #On remet l'alarme toutes les 10 minutes
    logger_log.info("Prochain reveil : 10 min")
               
#On arrête le programme
extinction()
