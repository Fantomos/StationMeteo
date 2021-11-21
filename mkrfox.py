from i2c import I2C

## Classe Mkrfox. 
#  Cette classe permet la communication avec le microcontrolleur Arduino MKRFOX 1200.
class Mkrfox:

    ## Constructeur.
    # @param pi Instance de pigpio.
    # @param logger Logger principal.
    # @param i2c_address Adresse I2C du MKRFOX 1200.
    # @param nb_try Nombres d'essais maximum de l'initialisation du bus I2C. La valeur par défaut est 5.
    def __init__(self, pi, i2c_address, logger, nb_try):
         ## Objet I2C initialisé.
        self.i2c_bus = I2C(pi, i2c_address, logger, nb_try)
        ## Logger principal.
        self.logger = logger

    
    ## Liste des nom des registres associés à leurs adresses et nombres d'octects.
    register =	{
            "time" : (0x00,4),
            "state" : (0x01,4),
            "error" : (0x02,4),
            "sleep" : (0x03,1),
            "wakeup" : (0x04,1),
            "sensorsData" : (0x05,12),
            "battery" : (0x06,4),
            "battery_threshold" :(0x07,4)
    }
   

    ## Opération de lecture d'un registre du MKRFOX.
    # @param regName Nom du registre à lire.
    # @param length Le nombre d'octet à lire.
    # @return Retourne la valeur du registre.
    def read(self, regName):
        return self.i2c_bus.readReg(self.register[regName][0], self.register[regName][1])
    
    ## Opération d'écriture d'un registre du MKRFOX.
    # @param regName Nom du registre à écrire.
    # @param data Les données à écrire.
    # @param length Le nombre d'octet à écrire.
    def write(self, regName, data):
        self.i2c_bus.writeReg(self.register[regName][0], data, self.register[regName][1])

    ## Formate les données des capteurs sous forme d'un tableau d'octet.
    # @param sensorsData Les données des capteurs.
    # @return Retourne un tableau d'octet.
    def formatData(self, sensorsData):
        try:
            data = []
            #Température
            #On passe la température de l'intervalle [-50; 205] à l'intervalle entier [0 ; 255] qu'on envoie en un octet
            data.append(abs(round(sensorsData['Temperature'])))

            #Humidité
            #On envoie l'humidité directement car elle est comprise entre 0 et 100
            data.append(round(sensorsData['Humidity']))

            #Pression
            #On envoie la pression de l'intervalle [800 ; 1453] en deux octects
            pression = round(sensorsData['Pressure'])
            data.append(pression // 256)
            data.append(pression % 256)

            #Vitesse du vent
            #On envoie la vitesse du vent de l'intervalle [0 ; 255] en un octet
            data.append(round(sensorsData['Speed']))
            data.append(round(sensorsData['Speed_max']))

            #Direction du vent
            #On envoie la direction entre [0 ; 360] en deux octects
            direction = round(sensorsData['Direction'])
            data.append(direction // 256)
            data.append(direction % 256)
            directionMax = round(sensorsData['Direction_max'])
            data.append(directionMax // 256)
            data.append(directionMax % 256)

            #Tension de la batterie
            #On convertie la tension en mV sur l'intervalle [0; 65536] en deux octets
            voltage = round(1000 * sensorsData['Battery'])
            data.append(voltage // 256)
            data.append(voltage % 256)

            return data 
        except:
            self.logger.error("Erreur lors du traitement des données pour l'envoi au réseau Sigfox.")
            
        
    ## Transmet les données des capteurs au MKRFOX.
    # @param sensorsData Les données des capteurs.
    def sendData(self, sensorsData):
        data = self.formatData(sensorsData)
        try:
            self.write("sensorsData", data)
        except:
            self.logger.error("Impossible d'envoyer des données au réseau Sigfox")
        else:
            self.logger.success("Envoie reussi au réseau Sigfox")
        