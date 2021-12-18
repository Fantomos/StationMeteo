
## @file sensors.py
# Définition de la classe Sensors. Elle permet la communication avec tous les capteurs connectés au Raspberry Pi.
##

from Adafruit_BMP.BMP085 import BMP085
from time import sleep, strftime,time
import math
import pigpio
from dht11 import DHT11
from threading import Thread

## Classe Sensors. 
# Cette classe permet la gestion de tous les capteurs connectés au Raspberry Pi.
class Sensors:

    ## Constructeur.
    # @param config Objet ConfigFile.
    # @param pi Intance pigpio
    # @param logger Logger principal.
    # @param logger_data Logger des données.
    # @param dht11_gpio Numéro de pin du capteur d'humidité DHT11. La valeur par défaut est 23.
    # @param init_nbtry Nombres d'essais maximum de l'initialisation des capteurs. La valeur par défaut est 5.
    # @param timeout Temps maximal pour réaliser une mesure.
    def __init__(self, config, pi, logger, logger_data, dht11_gpio = 23, init_nbtry = 5, timeout = 10):
        ##  Objet ConfigFile.
        self.config = config
        ## Instance pigpio
        self.pi = pi
        ##  Logger principal.
        self.logger = logger
        ##  Logger des données.
        self.logger_data = logger_data
        ##  Numéro de pin du capteur d'humidité DHT11.
        self.dht11_gpio = dht11_gpio
        ##  Nombres de mesures à réaliser à chaque lecture des capteurs.
        self.timeout = timeout
        self.logger.info("Tentative de connexion aux capteurs...")

        for i in range(init_nbtry):
            try:
                ## Référence du capteur de pression.
                self.barometre = BMP085() #On tente d'établir la connexion
            except Exception as e: #Si ça ne marche pas on attend avant de rententer
                self.barometre = None
                self.logger.error(e)
                self.logger.error("Impossible de se connecter au baromètre, essai " + str(i+1) + "/" + str(init_nbtry) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                self.logger.success("Baromètre connecté")
                break



    ## Lit la température via le thermomètre. Si le capteur ne répond pas, la lecture de la température est faite via le baromètre.
    # @param temperature Variable qui contiendra la réponse
    # @param nbmesures Nombre de mesure à effectuer
    def readThermometer(self, temperature):
        self.logger.info("Début des mesures du thermomètre...")
        start_time = time()
        while time()-start_time < self.timeout:
            try:
                h = self.pi.file_open("/sys/bus/w1/devices/28-00000adfb15d/w1_slave", pigpio.FILE_READ)
                c, data = self.pi.file_read(h, 500)
                self.pi.file_close(h)
                if type(data) is not str:
                    data = data.decode()
                if "YES" in data:
                    (discard, sep, reading) = data.partition(' t=')
                    if reading != 85000:
                        temperature.append(float(reading)/1000.0)
                        break
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de lire le thermomètre.")
                sleep(3)


        if len(temperature) == 0:
            self.logger.info("Prochain essai à l'aide du baromètre.")
            try:
                temperature.append(self.barometre.read_temperature())
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible d'obtenir la température.")

        self.logger.success("Lecture de la température terminée.")

    ## Lit la température et l'humidité via l'hygromètre.
    # @param Humidity Variable qui contiendra la réponse
    # @param nbmesures Nombre de mesure à effectuer
    def readHygrometer(self, humidity):
        self.logger.info("Début des mesures de l'humidité...")
        start_time = time()
        try:
            sensor = DHT11(self.pi, self.dht11_gpio)
            for d in sensor:
                h = d['humidity']
                if h <= 100 and h != 0:
                    humidity.append(h)
                    break
                if time()-start_time > self.timeout:
                    break
                sleep(1)
            sensor.close()
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire l'hygromètre.")

        self.logger.success("Lecture de l'humidité terminée.")

    ## Lit la pression via le baromètre.
    # @return Retourne la pression ou 0 en cas d'erreur.
    def readBarometer(self, pressure):
        self.logger.info("Début des mesures de la pression...")
        start_time = time()
        while time()-start_time < self.timeout:
            try:
                buffer = self.barometre.read_pressure()
                if buffer != 0:
                    pressure.append(buffer/100)
                    break
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de lire le baromètre.")
            sleep(1)

        self.logger.success("Lecture du baromètre terminée.")

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
        #Température, humidité, pression
        #Pour chaque grandeur, un thread met à jour le tableau avec les nouvelles mesures
        H,T,P = [], [],[]
        thread_hydro = Thread(target = Sensors.readHygrometer, args=(self,H))
        thread_temp = Thread(target = Sensors.readThermometer, args=(self,T))
        thread_press = Thread(target = Sensors.readBarometer, args=(self,P))
        thread_hydro.start()
        thread_temp.start()
        thread_press.start()
        thread_hydro.join()
        thread_temp.join()
        thread_press.join()

        #On renvoie un tableau contenant toutes les gradeurs moyennées
        rpiSensorsData = {"Time":strftime("%Hh%M"), "Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Cloud":self.getCloudBase(average(T), average(H))}
        return rpiSensorsData

   

        
## Calcule la moyenne d'un tableau
# @param arr Tableau à moyenner
# @return Retourne la moyenne du tableau ou 0 si le tableau est vide.
def average(arr):
    if(len(arr) == 0):
        return 0
    else:
        return sum(arr) / len(arr)

