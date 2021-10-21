from time import sleep
from smbus2 import SMBus


class Mkrfox:
    def __init__(self, i2c_bus, logger, i2c_address):
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.logger = logger
        self.register =	{
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "alarm_min_val" : 0x00,
            "alarm_sec_val" : 0x45
        }
   

    #Fonction permettant de lire la valeur d'un registre du PIC. Renvoie 100000 en cas d'erreur.
    def read(self, regName, length):
        return self.i2c_bus.readReg(self.i2c_address, regName, length)
    
    #Ecrit une valeur donnée (data) dans un registre donné (reg)
    def write(self, regName, data, length):
        self.i2c_bus.writeReg(self.i2c_address, self.register[regName], data, length)

    #Permet d'envoyer le tableau passé en argument à Sigfox
    def formatData(self, sensorsData):
        try:
            data = [1]
            #Température
            #On passe la température de l'intervalle [-100 ; 553] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if sensorsData['Temperature'] < 65536:
                temperature = round(100 * (sensorsData['Temperature'] + 100))
                data.append(temperature // 256)
                data.append(temperature % 256)
            else:
                data.append(255)
                data.append(255)
            #Humidité
            #On envoie l'humidité directement car elle est comprise entre 0 et 100
            data.append(round(sensorsData['Humidity']) if sensorsData['Humidity'] < 100000 else 255)
            #Pression
            #On passe la pression de l'intervalle [800 ; 1453] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if sensorsData['Pressure'] < 65536:
                pression = round(100 * (sensorsData['Pressure'] - 800))
                data.append(pression // 256)
                data.append(pression % 256)
            else:
                data.append(255)
                data.append(255)
            #Vitesse du vent
            #On passe la vitesse du vent de l'intervalle [0 ; 653] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if sensorsData['Speed'] < 65536:
                vitesse_vent = round(100 * sensorsData['Speed'])
                data.append(vitesse_vent // 256)
                data.append(vitesse_vent % 256)
            else:
                data.append(255)
                data.append(255)
            #Direction du vent
            #On l'envoie direction car elle est entre 0 et 16
            data.append(round(10 * sensorsData['Direction']) if sensorsData['Direction'] < 256 else 255)
            #Tension de la batterie
            data.append(int(10 * sensorsData['Voltage']))
            #Somme de contrôle qui vaut le mod 256 de la somme de tous les octets précédents
            somme = 0
            for i in range(len(data)):
                somme += data[i]
            somme = somme % 256
            data.append(somme)
            #Envoi
            return data 
        except:
            self.logger.error("Erreur lors du traitement des données pour l'envoi au réseau Sigfox.")
            
    #Fonction qui permet d'envoyer les données météo et de les mettre en forme
    def sendData(self, sensorsData):
        data = self.formatData(sensorsData)
        try:
            #On complète le tableau au cas où il fait moins de 12 octets
            len_data = len(data)
            data = data[0:self.message_length]
            data += [1] * (self.message_length - len_data)
            #On envoie les octets un par un par I2C
            for i in range(self.message_length):
                self.i2cbus.write_byte(self.i2c_address, data[i])
            self.logger.success("Envoie reussi au réseau Sigfox")
        except:
            self.logger.error("Impossible d'envoyer des données au réseau Sigfox")
        