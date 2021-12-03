from time import sleep
from i2c import I2C
## Classe Attiny.
# Cette classe permet la communication avec le microcontrolleur ATTINY.
class Attiny:
    ## Constructeur.
    # @param pi Instance de pigpio.
    # @param logger Logger principal.
    # @param i2c_address Adresse I2C de l'ATTINY.
    # @param nb_try Nombres d'essais maximum de l'initialisation du bus I2C. La valeur par défaut est 5.
    def __init__(self, pi, i2c_address, logger, nb_try):
        ## Objet I2C initialisé.
        self.i2c_bus = I2C(pi, i2c_address, logger, nb_try)
        ## Logger principal.
        self.logger = logger
    
    ## Opération d'écriture d'un registre du MKRFOX.
    # @param regName Nom du registre à écrire.
    # @param data Les données à écrire.
    # @param length Le nombre d'octet à écrire.
    def askRead(self):
        self.logger.info("Requête des données de vent à l'ATTINY")
        self.i2c_bus.writeReg(0x00, 0x11, 1)

    ## Opération de lecture de tous les registres de l'ATTINY.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre.
    def read(self, length):
        self.logger.info("Récupération des données de vent à l'ATTINY")
        return self.i2c_bus.readAll(length)
    
    def getWindData(self):
        wind_array = self.read(8)
        direction = int.from_bytes(wind_array[:2], byteorder='big', signed=False)/100
        speed = int.from_bytes(wind_array[2:4], byteorder='big', signed=False)
        direction_max = int.from_bytes(wind_array[4:6], byteorder='big', signed=False)/100
        speed_max = int.from_bytes(wind_array[6:8], byteorder='big', signed=False)
        return {"Direction": direction, "Speed":speed, "Direction_max":direction_max, "Speed_max":speed_max}
