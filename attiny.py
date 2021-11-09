
## Classe Attiny.
# Cette classe permet la communication avec le microcontrolleur ATTINY.
class Attiny:
    ## Constructeur.
    # @param i2c_bus Objet I2C initialisé.
    # @param logger Logger principal.
    # @param i2c_address Adresse I2C de l'ATTINY.
    def __init__(self, i2c_bus, logger, i2c_address):
        ## Objet I2C initialisé.
        self.i2c_bus = i2c_bus
        ## Adresse I2C de l'ATTINY.
        self.i2c_address = i2c_address
        ## Logger principal.
        self.logger = logger

    ## Liste des nom des registres et de leurs adresses.
    register =	{
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "alarm_min_val" : 0x00,
            "alarm_sec_val" : 0x45
    }

    
    def getWindData(self):
        return {"Direction":0, "Speed":0, "DirectionMax":0, "SpeedMax":0}
