

class Sigfox:
    def __init__(self, i2c_bus, logger, message_length = 12, i2c_address = 0x55):
        self.i2c_bus = i2c_bus
        self.message_length = message_length
        self.i2c_address = i2c_address
        self.logger = logger
        self.string_keys = {'site':0, 'altitude':1}
    
    #Permet d'envoyer le tableau passé en argument à Sigfox
    def sendMessageToSigFox(self, data):
        try:
            #On complète le tableau au cas où il fait moins de 12 octets
            len_data = len(data)
            data = data[0:self.message_length]
            data += [1] * (self.message_length - len_data)
            #On envoie les octets un par un par I2C
            for i in range(self.message_length):
                self.i2cbus.write_byte(self.i2c_address, data[i])
        except:
            self.logger.error("Impossible d'envoyer des données au réseau Sigfox")
            
    #Fonction qui permet d'envoyer les données météo et de les mettre en forme
    def sendValuesToSigFox(self, temperature, humidite, pression, vitesse_vent, direction_vent, tension_batterie, twitter):
        try:
            data = [1]
            #Température
            #On passe la température de l'intervalle [-100 ; 553] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if temperature < 65536:
                temperature = round(100 * (temperature + 100))
                data.append(temperature // 256)
                data.append(temperature % 256)
            else:
                data.append(255)
                data.append(255)
            #Humidité
            #On envoie l'humidité directement car elle est comprise entre 0 et 100
            data.append(round(humidite) if humidite < 100000 else 255)
            #Pression
            #On passe la pression de l'intervalle [800 ; 1453] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if pression < 65536:
                pression = round(100 * (pression - 800))
                data.append(pression // 256)
                data.append(pression % 256)
            else:
                data.append(255)
                data.append(255)
            #Vitesse du vent
            #On passe la vitesse du vent de l'intervalle [0 ; 653] à l'intervalle entier [0 ; 65536] qu'on envoie en deux octets
            if vitesse_vent < 65536:
                vitesse_vent = round(100 * vitesse_vent)
                data.append(vitesse_vent // 256)
                data.append(vitesse_vent % 256)
            else:
                data.append(255)
                data.append(255)
            #Direction du vent
            #On l'envoie direction car elle est entre 0 et 16
            data.append(round(10 * direction_vent) if direction_vent < 256 else 255)
            #Twitter
            data.append(100 if twitter else 255)
            #Tension de la batterie
            data.append(int(10 * tension_batterie))
            #Somme de contrôle qui vaut le mod 256 de la somme de tous les octets précédents
            somme = 0
            for i in range(len(data)):
                somme += data[i]
            somme = somme % 256
            data.append(somme)
            #Envoi
            self.sendMessageToSigFox(data)
        except:
            self.logger.error("Erreur lors du traitement des données pour l'envoi au réseau Sigfox.")
        
    #Fonction qui permet d'envoyer un string à un clé donnée
    def writeStringToSigFox(self, skey, string):
        try:
            string = string[0:self.message_length - 1]
            key = self.string_keys[skey]
            data = [100 + key]
            for i in range(len(string)):
                data.append(ord(string[i]))
            self.sendMessageToSigFox(data)
        except:
            self.logger.error("Impossible d'écrire un string par Sigfox.")
        
    #Fonction qui permet d'ajouter un string à un clé donnée
    def appendStringToSigFox(self, skey, string):
        try:
            string = string[0:self.message_length - 1]
            key = self.string_keys[skey]
            data = [150 + key]
            for i in range(len(string)):
                data.append(ord(string[i]))
            self.sendMessageToSigFox(data)
        except:
            self.logger.error("Impossible d'ajouter un string par Sigfox.")