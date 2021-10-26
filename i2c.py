from time import sleep
from smbus2 import SMBus

class I2C:
    def __init__(self, logger, mesures_nbtry = 5):
        self.logger = logger
        self.logger.info("Tentative de connexion au bus I2C...")
        for i in range(mesures_nbtry):
            try:
                self.i2cbus = SMBus(1) #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                logger.error("Impossible de se connecter au bus I2C, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                logger.success("Bus I2C connecté")
                break

    #Fonction permettant de lire la valeur d'un registre
    def readReg(self,i2c_address, reg, length):
        sleep(0.05) #Délai sinon ça marche pas
        try:
            buffer = self.i2cbus.read_i2c_block_data(i2c_address, reg, length)
            self.logger.success("Donnée reçu sur le registre" + str(reg))
            return int.from_bytes(buffer, byteorder='big', signed=False) 
        except:
            self.logger.error("Impossible de lire le registre " + str(reg) + " sur le PIC.")
            return 0

    #Fonction permettant d'ecrire la valeur dans un registre
    def writeReg(self, i2c_address, reg, data, length):
        try:
            self.i2cbus.write_i2c_block_data(i2c_address, reg, data.to_bytes(length, 'big'))
            self.logger.success("Donnée transmise sur le registre" + str(reg) + ", données=" + str(data) + ")")
        except:
            self.logger.error("Impossible d'envoyer les données sur le registre " + str(reg) + ", données=" + str(data) + ")")
