from imports import *

#Permet d'envoyer le tableau passé en argument à Sigfox
def sendMessageToSigFox(data):
    try:
        #On complète le tableau au cas où il fait moins de 12 octets
        len_data = len(data)
        data = data[0:sigfox_mes_len]
        data += [1] * (sigfox_mes_len - len_data)
        #On envoie les octets un par un par I2C
        for i in range(sigfox_mes_len):
            bus.write_byte(sigfox_addr, data[i])
    except:
        logger.error("Impossible d'envoyer des données au Sigfox")
        
#Fonction qui permet d'envoyer les données météo et de les mettre en forme
def sendValuesToSigFox(temperature, humidite, pression, vitesse_vent, direction_vent, tension_batterie, twitter):
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
        for i in range(11):
            somme += data[i]
        somme = somme % 256
        data.append(somme)
        #Envoi
        sendMessageToSigFox(data)
    except:
        logger.error("Erreur lors du traitement des données pour l'envoi à Sigfox.")
    
#Fonction qui permet d'envoyer un string à un clé donnée
def writeStringToSigFox(skey, string):
    try:
        string = string[0:sigfox_mes_len - 1]
        key = string_keys[skey]
        data = [100 + key]
        for i in range(len(string)):
            data.append(ord(string[i]))
        sendMessageToSigFox(data)
    except:
        logger.error("Impossible d'écrire un string par Sigfox.")
    
#Fonction qui permet d'ajouter un string à un clé donnée
def appendStringToSigFox(skey, string):
    try:
        string = string[0:sigfox_mes_len - 1]
        key = string_keys[skey]
        data = [150 + key]
        for i in range(len(string)):
            data.append(ord(string[i]))
        sendMessageToSigFox(data)
    except:
        logger.error("Impossible d'append un string par Sigfox.")