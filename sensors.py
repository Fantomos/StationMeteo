import Adafruit_BMP.BMP085 as BMP
import Adafruit_DHT as DHT
from w1thermsensor import W1ThermSensor
from time import sleep
import math
from config import *
from pic import readPicData, resetWatchdogTimer


#Permet de lire la température via le thermomètre. Si il y a un problème, on renvoie plutôt la température donnée par le baromètre. Si lui aussi a une erreur, on renvoie 100000.
def readThermometer(thermometre, barometre):
    try:
        return thermometre.get_temperature()
    except:
        try:
            return barometre.read_temperature()
        except:
            logger_log.error("Impossible de lire le thermomètre.")
            return 100000

#Permet de lire la température et l'humidité via l'hygromètre. Renvoie 100000 en cas d'erreur.
def readHygrometer(hygrometre):
    try:
        return DHT.read_retry(hygrometre, dht11_gpio)
    except:
        logger_log.error("Impossible de lire l'hygromètre.")
        return 100000, 100000

#Permet de lire la pression et l'altitude via le baromètre. Renvoie 100000 en cas d'erreur.
def readBarometer(barometre):
    try:
        return barometre.read_pressure(), barometre.read_altitude()
    except:
        logger_log.error("Impossible de lire le baromètre.")
        return 100000, 100000


#Connexionà l'hygromètre
def initHygrometer():
    for i in range(mesures_nbtry):
        try:
            hygrometre = DHT.DHT11
        except: #Si ça ne marche pas on attend avant de rententer
            logger_log.error("Impossible de se connecter à l'hygromètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger_log.success("Thermomètre connecté")
            break
    return hygrometre
    


#Connexion au thermomètre
def initThermometer():
    for i in range(mesures_nbtry):
        try:
            thermometre = W1ThermSensor() #On tente d'établir la connexion
        except: #Si ça ne marche pas on attend avant de rententer
            logger_log.error("Impossible de se connecter au thermomètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger_log.success("Thermomètre connecté")
            break
    return thermometre
    
#Connection au baromètre  
def initBarometer():
    for i in range(mesures_nbtry):
        try:
            barometre = BMP.BMP085() #On tente d'établir la connexion
        except: #Si ça ne marche pas on attend avant de rententer
            logger_log.error("Impossible de se connecter au baromètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger_log.success("Baromètre connecté")
            break
    return barometre

#Fonction qui permet de calculer la hauteur de la base des nuages grâce à l'approximation de Magnus-Tetens
def getCloudBase(T, H):
    try:
        phi = H / 100
        alpha = nuages_dewa * T/(nuages_dewb + T) + math.log(phi)
        dew_point = (nuages_dewb * alpha)/(nuages_dewa - alpha)
        return nuages_K * (T - dew_point)
    except:
        logger_log.error("Impossible de calculer la hauteur de la base des nuages.")
        return 0
    
def average(arr):
    return sum(arr) / len(arr)

#Fonction qui permet de lire toutes les valeurs des capteurs et de tout renvoyer en un seul tableau.
def getSensorsData():
    #Température, humidité, pression, altitude
    #Pour chaque grandeur, on l'ajoute au tableau seulement si elle n'est pas trop grande, ce qui indiquerait un problème de mesure
    T, H, P, A = [], [], [], []
    logger_log.info("Début des mesures")
    for i in range(mesures_nbmesures):
        temp = readThermometer()
        if temp < 65536:
            T.append(temp)
        temp = readHygrometer()[0]
        if temp < 256:
            H.append(temp)
        donnees_baro = readBarometer()
        if donnees_baro[0]/100 < 65536:
            P.append(donnees_baro[0]/100)
        if donnees_baro[1] < 65536:
            A.append(donnees_baro[1])
        sleep(0.1)
        print(i)
        resetWatchdogTimer()
    
    windData = readPicData() #On lit les données du PIC
    #windData = [16, 0.0]
    
    #On renvoie un tableau contenant toutes les gradeurs moyennées
    sensorsData = {"Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Altitude":average(A), "Cloud":getCloudBase(average(T), average(H)), "Direction":windData[0], "Speed":windData[1], "DirectionMax":windData[2], "SpeedMax":windData[3]}
    logger_data.info(",".join([str(d) for d in sensorsData]))

    return sensorsData

   

        

