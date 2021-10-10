from Adafruit_BMP.BMP085 import BMP085
import Adafruit_DHT as DHT
from w1thermsensor import W1ThermSensor
from time import sleep, time
import math


class Sensors:
    def __init__(self, config, logger, logger_data, pic, dht11_gpio, mesures_nbtry, nbmesures):
        self.config = config
        self.logger = logger
        self.logger_data = logger_data
        self.pic = pic
        self.dht11_gpio = dht11_gpio
        self.nbmesures = nbmesures
        for i in range(mesures_nbtry):
            try:
                self.hygrometre = DHT.DHT11
            except: #Si ça ne marche pas on attend avant de rententer
                self.hygrometre = None
                self.logger.error("Impossible de se connecter à l'hygromètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Thermomètre connecté")
                break

        for i in range(mesures_nbtry):
            try:
                self.thermometre = W1ThermSensor() #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                self.thermometre = None
                self.logger.error("Impossible de se connecter au thermomètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Thermomètre connecté")
                break

        for i in range(mesures_nbtry):
            try:
                self.barometre = BMP085() #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                self.barometre = None
                self.logger.error("Impossible de se connecter au baromètre, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
                sleep(1)
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
                return 100000

    #Permet de lire la température et l'humidité via l'hygromètre. Renvoie 100000 en cas d'erreur.
    def readHygrometer(self):
        try:
            return DHT.read_retry(self.hygrometre, self.dht11_gpio)
        except:
            self.logger.error("Impossible de lire l'hygromètre.")
            return 100000, 100000

    #Permet de lire la pression et l'altitude via le baromètre. Renvoie 100000 en cas d'erreur.
    def readBarometer(self):
        try:
            return self.barometre.read_pressure(), self.barometre.read_altitude()
        except:
            self.logger.error("Impossible de lire le baromètre.")
            return 100000, 100000


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
    def getSensorsData(self):
        #Température, humidité, pression, altitude
        #Pour chaque grandeur, on l'ajoute au tableau seulement si elle n'est pas trop grande, ce qui indiquerait un problème de mesure
        T, H, P, A = [], [], [], []
        self.logger.info("Début des mesures")
        for i in range(self.nbmesures):
            temp = self.readThermometer()
            if temp < 65536:
                T.append(temp)
            temp = self.readHygrometer()[0]
            if temp < 256:
                H.append(temp)
            donnees_baro = self.readBarometer()
            if donnees_baro[0]/100 < 65536:
                P.append(donnees_baro[0]/100)
            if donnees_baro[1] < 65536:
                A.append(donnees_baro[1])
            sleep(0.1)
            print(i)
            #resetWatchdogTimer()
        
        wind_data = self.pic.readPicData() #On lit les données du PIC
        battery_voltage = self.pic.readPicReg("battery")/10
        #windData = [16, 0.0]
        
        #On renvoie un tableau contenant toutes les gradeurs moyennées
        sensorsData = {"Time":time.strftime("%Hh%M"),"Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Altitude":average(A), "Cloud":self.getCloudBase(average(T), average(H)), "Direction":wind_data[0], "Speed":wind_data[1], "Direction_max":wind_data[2], "Speed_max":wind_data[3], "Voltage":battery_voltage}
        self.logger_data.info(",".join([str(d) for d in sensorsData]))

        return sensorsData

   

        
        
def average(arr):
    return sum(arr) / len(arr)

