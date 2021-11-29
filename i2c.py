from time import sleep

## Classe I2C. 
#  Cette classe permet la communication à partir d'un bus I2C.
class I2C:

    ## Constructeur.
    # @param pi Instance de pigpio.
    # @param logger Logger principal.
    # @param i2c_address L'addresse I2C de l'appareil esclave.
    # @param nb_try Nombres d'essais maximum de l'initialisation du bus I2C. La valeur par défaut est 5.
    def __init__(self, pi, i2c_address, logger, nb_try = 5):
        ## Logger principal.
        self.logger = logger
        ## Instance de pigpio
        self.pi = pi
        self.logger.info("Tentative de connexion au bus I2C...")
        for i in range(nb_try):
            try:
                ## Référence de la connexion I2C.
                self.handle = self.pi.i2c_open(1, i2c_address) # On tente d'établir la connexion
            except Exception as e: #Si ça ne marche pas on attend avant de rententer
                logger.error(e)
                logger.error("Impossible de se connecter au bus I2C, essai " + str(i) + "/" + str(nb_try) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                logger.success("Bus I2C connecté")
                break

    ## Opération de lecture d'un registre sur le bus I2C.
  
    # @param reg L'adresse du registre à lire.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre ou 0 en cas d'erreur.
    def readReg(self, reg, length):
        try:
            sleep(1)
            self.pi.i2c_write_device(self.handle, [reg])
            sleep(1)
            buffer = self.pi.i2c_read_device(self.handle, length)
            self.logger.success("Données " + str(buffer[1]) + " reçues sur le registre " + str(reg))
            return int.from_bytes(buffer[1], byteorder='big', signed=False) 
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire le registre " + str(reg))
            return 0

    ## Opération de lecture de tous les registres sur le bus I2C.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur des registres ou 0 en cas d'erreur.
    def readAll(self, length):
        try:
            sleep(1)
            buffer = self.pi.i2c_read_device(self.handle, length)
            self.logger.success("Données " + str(buffer[1]) + " reçues")
            return buffer[1]
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible de lire les registres")
            return bytearray([0] * length)

    ## Opération d'écriture d'un registre sur le bus I2C.
    # @param reg L'adresse du registre à écrire.
    # @param data Les données à écrire dans le registre.
    # @param length Le nombre d'octet à écrire.
    def writeReg(self, reg, data, length):
        try:
            if isinstance(data, list):
                data_array = bytearray(data)
            else:
                data_array = bytearray(data.to_bytes(length, 'big'))
            data_array.insert(0, reg)
            sleep(1)
            self.pi.i2c_write_device(self.handle, data_array)
            self.logger.success("Données transmises sur le registre " + str(reg) + ", données=" + str(data) + ")")
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible d'envoyer les données sur le registre " + str(reg) + ", données=" + str(data) + ")")