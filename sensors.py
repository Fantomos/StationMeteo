from Adafruit_BMP.BMP085 import BMP085
import Adafruit_DHT as DHT
from w1thermsensor import W1ThermSensor
import time
import math


class Sensors:
    def __init__(self, config, logger, logger_data, dht11_gpio, mesures_nbtry, nbmesures):
        self.config = config
        self.logger = logger
        self.logger_data = logger_data
        self.dht11_gpio = dht11_gpio
        self.nbmesures = nbmesures
        self.logger.info("Tentative de connexion aux capteurs...")
        for i in range(mesures_nbtry):
            try:
                self.hygrometre = DHT.DHT11
            except: #Si ça ne marche pas on attend avant de rententer
                self.hygrometre = None
                self.logger.error("Impossible de se connecter à l'hygromètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Hygromètre connecté")
                break

        for i in range(mesures_nbtry):
            try:
                self.thermometre = W1ThermSensor() #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                self.thermometre = None
                self.logger.error("Impossible de se connecter au thermomètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Thermomètre connecté")
                break

        for i in range(mesures_nbtry):
            try:
                self.barometre = BMP085() #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                self.barometre = None
                self.logger.error("Impossible de se connecter au baromètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Baromètre connecté")
                break



    #Permet de lire la température via le thermomètre. Si il y a un problème, on renvoie plutôt la température donnée par le baromètre. Si lui aussi a une erreur, on renvoie 100000.
    def readThermometer(self):
        try:
            return self.thermometre.get_temperature()
        except:
            try:
                return self.barometre.read_temperature()
            except:
                self.logger.error("Impossible de lire le thermomètre.")
                return 0

    #Permet de lire la température et l'humidité via l'hygromètre. Renvoie 100000 en cas d'erreur.
    def readHygrometer(self):
        try:
            return DHT.read_retry(self.hygrometre, self.dht11_gpio)
        except:
            self.logger.error("Impossible de lire l'hygromètre.")
            return 0, 0

    #Permet de lire la pression et l'altitude via le baromètre. Renvoie 100000 en cas d'erreur.
    def readBarometer(self):
        try:
            return self.barometre.read_pressure(), self.barometre.read_altitude()
        except:
            self.logger.error("Impossible de lire le baromètre.")
            return 0, 0


    #Fonction qui permet de calculer la hauteur de la base des nuages grâce à l'approximation de Magnus-Tetens
    def getCloudBase(self, T, H, nuages_dewb = 237.7, nuages_dewa = 17.27, nuages_K = 122.7):
        try:
            phi = H / 100
            alpha = nuages_dewa * T/(nuages_dewb + T) + math.log(phi)
            dew_point = (nuages_dewb * alpha)/(nuages_dewa - alpha)
            return nuages_K * (T - dew_point)
        except:
            self.logger.error("Impossible de calculer la hauteur de la base des nuages.")
            return 0


    #Fonction qui permet de lire toutes les valeurs des capteurs et de tout renvoyer en un seul tableau.
    def getRPISensorsData(self):
        #Température, humidité, pression, altitude
        #Pour chaque grandeur, on l'ajoute au tableau seulement si elle n'est pas trop grande, ce qui indiquerait un problème de mesure
        T, H, P, A = [], [], [], []
        for i in range(self.nbmesures):
            self.logger.info("Début des mesures : " + str(i+1) +"/"+ str(self.nbmesures))
            temp = self.readThermometer()
            if temp != 0:
                T.append(temp)
            humi = self.readHygrometer()[0]
            if humi is not None and humi != 0:
                H.append(humi)
            donnees_baro = self.readBarometer()
            if donnees_baro[0]/100 != 0:
                P.append(donnees_baro[0]/100)
            if donnees_baro[1] != 0:
                A.append(donnees_baro[1])
        
        #On renvoie un tableau contenant toutes les gradeurs moyennées
        rpiSensorsData = {"Time":time.strftime("%Hh%M"), "Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Altitude":average(A), "Cloud":self.getCloudBase(average(T), average(H))}

        return rpiSensorsData

   

        
        
def average(arr):
    if(len(arr) == 0):
        return 0
    else:
        return sum(arr) / len(arr)

