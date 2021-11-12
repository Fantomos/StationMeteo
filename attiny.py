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

    ## Opération de lecture de tous les registres de l'ATTINY.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre.
    def read(self, length):
        return self.i2c_bus.readAll(length)
    
    def getWindData(self):
        return {"Direction":0, "Speed":0, "DirectionMax":0, "SpeedMax":0}
