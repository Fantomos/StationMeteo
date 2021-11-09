from time import sleep
from smbus2 import SMBus

## Classe I2C. 
#  Cette classe permet la communication à partir d'un bus I2C.
#  Utilise la bibliothèque smbus2.
class I2C:

    ## Constructeur.
    # @param logger Logger principal.
    # @param nb_try Nombres d'essais maximum de l'initialisation du bus I2C. La valeur par défaut est 5.
    def __init__(self, logger, nb_try = 5):
        ## Logger principal.
        self.logger = logger
        self.logger.info("Tentative de connexion au bus I2C...")
        for i in range(nb_try):
            try:
                ## Référence du bus I2C.
                self.i2cbus = SMBus(1) #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                logger.error("Impossible de se connecter au bus I2C, essai " + str(i) + "/" + str(nb_try) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                logger.success("Bus I2C connecté")
                break

    ## Opération de lecture d'un registre sur le bus I2C.
    # @param i2c_address L'addresse I2C de l'appareil esclave.
    # @param reg L'adresse du registre à lire.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre ou 0 en cas d'erreur.
    def readReg(self,i2c_address, reg, length):
        sleep(0.05) #Délai sinon ça marche pas
        try:
            buffer = self.i2cbus.read_i2c_block_data(i2c_address, reg, length)
            self.logger.success("Donnée " + str(buffer) + " reçu sur le registre " + str(reg))
            return int.from_bytes(buffer, byteorder='big', signed=False) 
        except:
            self.logger.error("Impossible de lire le registre " + str(reg) + " sur le PIC.")
            return 0

    ## Opération d'écriture d'un registre sur le bus I2C.
    # @param i2c_address L'addresse I2C de l'appareil esclave.
    # @param reg L'adresse du registre à écrire.
    # @param data Les données à écrire dans le registre.
    # @param length Le nombre d'octet à écrire.
    def writeReg(self, i2c_address, reg, data, length):
        try:
            self.i2cbus.write_i2c_block_data(i2c_address, reg, data.to_bytes(length, 'big'))
            self.logger.success("Donnée transmise sur le registre " + str(reg) + ", données=" + str(data) + ")")
        except:
            self.logger.error("Impossible d'envoyer les données sur le registre " + str(reg) + ", données=" + str(data) + ")")
