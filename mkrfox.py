from time import sleep

class Mkrfox:
    def __init__(self, i2c_bus, logger, i2c_address):
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.logger = logger

    
    register =	{
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "time" : 0x00,
            "state" : 0x45,
            "sensorsData" : 0x46
    }
   

    #Fonction permettant de lire la valeur d'un registre du PIC. Renvoie 100000 en cas d'erreur.
    def read(self, regName, length):
        return self.i2c_bus.readReg(self.i2c_address, register[regName], length)
    
    #Ecrit une valeur donnée (data) dans un registre donné (reg)
    def write(self, regName, data, length):
        self.i2c_bus.writeReg(self.i2c_address, register[regName], data, length)

    #Permet d'envoyer le tableau passé en argument à Sigfox
    def formatData(self, sensorsData):
        try:
            data = []
            #Température
            #On passe la température de l'intervalle [-50; 205] à l'intervalle entier [0 ; 255] qu'on envoie en un octet
            data.append(abs(round(sensorsData['Temperature']) + 50))

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
            data.append(round(sensorsData['SpeedMax']))

            #Direction du vent
            #On envoie la direction entre [0 ; 360] en deux octects
            direction = round(sensorsData['Direction'])
            data.append(direction // 256)
            data.append(direction % 256)
            directionMax = round(sensorsData['DirectionMax'])
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
            
    #Fonction qui permet d'envoyer les données météo et de les mettre en forme
    def sendData(self, sensorsData):
        data = self.formatData(sensorsData)
        try:
            self.write("sensorsData", data, 12)
        except:
            self.logger.error("Impossible d'envoyer des données au réseau Sigfox")
        else:
            self.logger.success("Envoie reussi au réseau Sigfox")
        