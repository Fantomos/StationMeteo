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

    ## Liste des nom des registres et de leurs adresses.
    register =	{
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "alarm_min_val" : 0x00,
            "alarm_sec_val" : 0x45
    }

    ## Opération de lecture d'un registre du MKRFOX.
    # @param regName Nom du registre à lire.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre.
    def read(self, regName, length):
        return self.i2c_bus.readReg(self.i2c_address, self.register[regName], length)
    
    ## Opération d'écriture d'un registre du MKRFOX.
    # @param regName Nom du registre à écrire.
    # @param data Les données à écrire.
    # @param length Le nombre d'octet à écrire.
    def write(self, regName, data, length):
        self.i2c_bus.writeReg(self.i2c_address, self.register[regName], data, length)
    
    def getWindData(self):
        return {"Direction":0, "Speed":0, "DirectionMax":0, "SpeedMax":0}
