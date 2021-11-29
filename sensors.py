from Adafruit_BMP.BMP085 import BMP085
import Adafruit_DHT as DHT
from w1thermsensor import W1ThermSensor
import time
import math

## Classe Sensors. 
# Cette classe permet la gestion de tous les capteurs connectés au Raspberry Pi.
class Sensors:

    ## Constructeur.
    # @param config Objet ConfigFile.
    # @param logger Logger principal.
    # @param logger_data Logger des données.
    # @param dht11_gpio Numéro de pin du capteur d'humidité DHT11. La valeur par défaut est 23.
    # @param mesures_nbtry Nombres d'essais maximum de l'initialisation des capteurs. La valeur par défaut est 5.
    # @param nbmesures Nombres de mesures à réaliser à chaque lecture des capteurs. La valeur par défaut est 3.
    def __init__(self, config, logger, logger_data, dht11_gpio = 23, mesures_nbtry = 5, nbmesures = 3):
        ##  Objet ConfigFile.
        self.config = config
        ##  Logger principal.
        self.logger = logger
        ##  Logger des données.
        self.logger_data = logger_data
        ##  Numéro de pin du capteur d'humidité DHT11.
        self.dht11_gpio = dht11_gpio
        ##  Nombres de mesures à réaliser à chaque lecture des capteurs.
        self.nbmesures = nbmesures
        self.logger.info("Tentative de connexion aux capteurs...")
        for i in range(mesures_nbtry):
            try:
                ## Référence du capteur d'humidité DHT11.
                self.hygrometre = DHT.DHT11
            except : #Si ça ne marche pas on attend avant de rententer
                self.hygrometre = None
                self.logger.error("Impossible de se connecter à l'hygromètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Hygromètre connecté")
                break

        


        for i in range(mesures_nbtry):
            try:
                ## Référence du capteur de température.
                self.thermometre = W1ThermSensor() #On tente d'établir la connexion
            except Exception as e: #Si ça ne marche pas on attend avant de rententer
                self.thermometre = None
                self.logger.error(e)
                self.logger.error("Impossible de se connecter au thermomètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Thermomètre connecté")
                break

        for i in range(mesures_nbtry):
            try:
                ## Référence du capteur de pression.
                self.barometre = BMP085() #On tente d'établir la connexion
            except Exception as e: #Si ça ne marche pas on attend avant de rententer
                self.barometre = None
                self.logger.error(e)
                self.logger.error("Impossible de se connecter au baromètre, essai " + str(i+1) + "/" + str(mesures_nbtry) + ".")
                time.sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Baromètre connecté")
                break



    ## Lit la température via le thermomètre. Si le capteur ne répond pas, la lecture de la température est faite via le baromètre.
    # @return Retourne la température ou 0 en cas d'erreur.
    def readThermometer(self):
        try:
            return self.thermometre.get_temperature()
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire le thermomètre. Prochain essai à l'aide du baromètre.")
            try:
                return self.barometre.read_temperature()
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de lire le thermomètre.")
                return 0

    ## Lit la température et l'humidité via l'hygromètre.
    # @return Retourne la température et l'humidité ou 0,0 en cas d'erreur.
    def readHygrometer(self):
        try:
            return DHT.read_retry(self.hygrometre, self.dht11_gpio)
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire l'hygromètre.")
            return 0, 0

    ## Lit la pression via le baromètre.
    # @return Retourne la pression ou 0 en cas d'erreur.
    def readBarometer(self):
        try:
            return self.barometre.read_pressure()
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire le baromètre.")
            return 0


    ## Calcule la hauteur de la base des nuages grâce à l'approximation de Magnus-Tetens.
    # @param T Température.
    # @param H Humidité.
    # @param nuages_dewb Constante dewb. La valeur par défaut est 237,7.
    # @param nuages_dewa Constante dewa. La valeur par défaut est 17,27.
    # @param nuages_K Constante K. La valeur par défaut est 122,7.
    # @return Retourne l'altitude des nuages ou 0 en cas d'erreur..
    def getCloudBase(self, T, H, nuages_dewb = 237.7, nuages_dewa = 17.27, nuages_K = 122.7):
        try:
            phi = H / 100
            alpha = nuages_dewa * T/(nuages_dewb + T) + math.log(phi)
            dew_point = (nuages_dewb * alpha)/(nuages_dewa - alpha)
            return nuages_K * (T - dew_point)
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de calculer la hauteur de la base des nuages.")
            return 0


    ## Lit tous les capteurs et formates le résultat sous la forme d'un dictionnaire.
    # @return Retourne le dictionnaire contenant les données des capteurs.
    def getRPISensorsData(self):
        #Température, humidité, pression, altitude
        #Pour chaque grandeur, on l'ajoute au tableau seulement si elle n'est pas trop grande, ce qui indiquerait un problème de mesure
        T, H, P = [], [], []
        for i in range(self.nbmesures):
            self.logger.info("Début des mesures : " + str(i+1) +"/"+ str(self.nbmesures))
            temp = self.readThermometer()
            if temp != 0:
                T.append(temp)
            humi = self.readHygrometer()[0]
            if humi is not None and humi != 0:
                H.append(humi)
            donnees_baro = self.readBarometer()
            if donnees_baro/100 != 0:
                P.append(donnees_baro/100)

        
        #On renvoie un tableau contenant toutes les gradeurs moyennées
        rpiSensorsData = {"Time":time.strftime("%Hh%M"), "Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Cloud":self.getCloudBase(average(T), average(H))}
        return rpiSensorsData

   

        
## Calcule la moyenne d'un tableau
# @param arr Tableau à moyenner
# @return Retourne la moyenne du tableau ou 0 si le tableau est vide.
def average(arr):
    if(len(arr) == 0):
        return 0
    else:
        return sum(arr) / len(arr)

