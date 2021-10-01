from imports import *
import pic
import config
import calendar
import time

#Permet de lire la température via le thermomètre. Si il y a un problème, on renvoie plutôt la température donnée par le baromètre. Si lui aussi a une erreur, on renvoie 100000.
def readThermometer():
    try:
        return thermometre.get_temperature()
    except:
        try:
            return barometre.read_temperature()
        except:
            logger.error("Impossible de lire le thermomètre.")
            return 100000

#Permet de lire la température et l'humidité via l'hygromètre. Renvoie 100000 en cas d'erreur.
def readHygrometer():
    try:
        return DHT.read_retry(hygrometre, DHT11_pin)
    except:
        logger.error("Impossible de lire l'hygromètre.")
        return 100000, 100000

#Permet de lire la pression et l'altitude via le baromètre. Renvoie 100000 en cas d'erreur.
def readBarometer():
    try:
        return barometre.read_pressure(), barometre.read_altitude()
    except:
        logger.error("Impossible de lire le baromètre.")
        return 100000, 100000


#Connexionà l'hygromètre
def initHygrometer(n_try):
    for i in range(n_try):
        try:
            hygrometre = DHT.DHT11
        except: #Si ça ne marche pas on attend avant de rententer
                logger.error("Impossible de se connecter à l'hygromètre, essai " + str(i) + "/" + str(n_try) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger.success("Thermomètre connecté")
            break
    return hygrometre
    


#Connexion au thermomètre
def initThermometer(n_try):
    for i in range(n_try):
        try:
            thermometre = W1ThermSensor() #On tente d'établir la connexion
        except: #Si ça ne marche pas on attend avant de rententer
            logger.error("Impossible de se connecter au thermomètre, essai " + str(i) + "/" + str(n_try) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger.success("Thermomètre connecté")
            break
    return thermometre
    
#Connection au baromètre  
def initBarometer(n_try):
    for i in range(n_try):
        try:
            barometre = BMP.BMP085() #On tente d'établir la connexion
        except: #Si ça ne marche pas on attend avant de rententer
            logger.error("Impossible de se connecter au baromètre, essai " + str(i) + "/" + str(n_try) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger.success("Baromètre connecté")
            break
    return barometre
    
def initI2C(n_try):
    for i in range(n_try):
        try:
            bus = smbus2.SMBus(1) #On tente d'établir la connexion
        except: #Si ça ne marche pas on attend avant de rententer
            logger.error("Impossible de se connecter au bus I2C, essai " + str(i) + "/" + str(n_try) + ".")
            sleep(1)
        else: #Si ça marche on sort de la boucle
            logger.success("Bus I2C connecté")
            break
    return bus

#Fonction qui permet de calculer la hauteur de la base des nuages grâce à l'approximation de Magnus-Tetens
def getCloudBase(T, H):
    try:
        phi = H / 100
        alpha = dew_a * T/(dew_b + T) + math.log(phi)
        dew_point = (dew_b * alpha)/(dew_a - alpha)
        return nuages_K * (T - dew_point)
    except:
        logger.error("Impossible de calculer la hauteur de la base des nuages.")
        return 0
    
def average(arr):
    return sum(arr) / len(arr)

#Fonction qui permet de lire toutes les valeurs des capteurs et de tout renvoyer en un seul tableau.
def getSensorsData():
    #Température, humidité, pression, altitude
    #Pour chaque grandeur, on l'ajoute au tableau seulement si elle n'est pas trop grande, ce qui indiquerait un problème de mesure
    T, H, P, A = [], [], [], []
    logger.info("Début des mesures")
    for i in range(n_mesures):
        temp = readThermometer()
        if temp < 65536:
            T.append(temp)
        temp = readHygrometer()[0]
        if temp < 256:
            H.append(temp)
        donnees_baro = readBarometer()
        if donnees_baro[0]/100 < 65536:
            P.append(donnees_baro[0]/100)
        if donnees_baro[1] < 65536:
            A.append(donnees_baro[1])
        sleep(0.1)
        print(i)
        pic.resetWatchdogTimer()
    
    windData = pic.readData() #On lit les données du PIC
    #windData = [16, 0.0]
    
    #On renvoie un tableau contenant toutes les gradeurs moyennées
    sensorsData = {"Temperature":average(T),"Humidity":average(H),"Pressure":average(P), "Altitude":average(A), "Cloud":getCloudBase(average(T), average(H)), "Direction":windData[0], "Speed":windData[1], "DirectionMax":windData[2], "SpeedMax":windData[3]}
    saveData(sensorsData)
    return sensorsData

#Enregistre les données dans le fichier data_file, en ne gardant que les 3 dernières fois (30 minutes)
#On enregistre également les données dans un autre fichier qui lui ne va pas les supprimer, pour garder une trace de tout
def saveData(data_in):
    try:
    #Si une des données est fausse, on enregistre rien
        data = data_in.copy()
        for d in data:
            if d > 80000:
                return False
        #Si le fichier n'existe pas, on le crée
        if not os.path.isfile(data_file):
            open(data_file,"x").close()
        #On ouvre le fichier et on enlève les lignes vides
        file = open(data_file, "r+")
        lines = list(filter(lambda a: a != "", file.read().split("\n")))
        #Si il y a moins de 6 données, on ajoute juste les nouvelles
        if len(lines) < saved_data_count:
            lines.append(",".join([str(d) for d in data]))
        else: #Sinon, on enlève la première et on ajoute la nouvelle
            lines = lines[1:]
            lines.append(",".join([str(d) for d in data]))
        #On se place au début du fichier, et on overwrite avec les nouvelles données
        file.seek(0)
        file.write("\n".join(lines))
        file.close()
        
        #Si le fichier data_file_all n'existe pas, on le créé
        if not os.path.isfile(data_file_all):
            open(data_file_all, "x").close()
        #On écrit les données séparées par des virgules en ajoutant l'heure à laquelle elles ont été mesurées
        file = open(data_file_all, "a+")
        data.insert(0, calendar.timegm(time.gmtime()))
        file.write(",".join([str(d) for d in data]) + "\n")
        file.close()
    except:
        logger.error("Erreur pendant la sauvegarde des données.")

#Renvoie la vitesse moyenne et max ainsi que la direction moyenne et max du vent sur les dernières données
def getAverageAndMaxData(data_in):
    try:
        if not os.path.isfile(data_file): #Si le fichier n'existe pas on renvoie des fausses valeurs
            return [100000, 100000, 100000, 100000]
        else:
            #On ouvre le fichier et on enlève les lignes vides
            file = open(data_file, "r+")
            lines = list(filter(lambda a: a!= "", file.read().split("\n")))
            wind_speeds = []
            max_wind_speed = 0
            max_wind_speed_dir = 0
            wind_dirs = []
            #On parcourt les lignes du fichier, en récupérant la vitesse et la direction du vent
            #avec des sécurités sur la lecture des données, en cas de mauvais format
            for line in lines:
                ws_str = line.split(",")[6]
                if len(ws_str.split(".")) > 2:wind_speeds.append(float(ws_str.split(".")[-2]+"."+ws_str.split(".")[-1]))
                else:wind_speeds.append(float(ws_str))
                wd_str = line.split(",")[5]
                #wind_speeds.append(float(line.split(",")[6].replace("0.0.","0."))) #On stocke la vitesse du vent
                if wind_speeds[-1] > max_wind_speed: #Si elle est supérieur au max, on stocke le nouveau max ainsi que la direction associée
                    max_wind_speed = wind_speeds[-1]
                    max_wind_speed_dir = int(wd_str) if wd_str.isnumeric() else 16 #int(line.split(",")[5])
                wind_dirs.append(int(wd_str) if wd_str.isnumeric() else 16) #On stocke la direction du vent
            #On renvoie [direction moy, direction max, vitesse moy, vitesse max]
            return [max(set(wind_dirs), key=wind_dirs.count), max_wind_speed_dir, sum(wind_speeds)/len(wind_speeds), max_wind_speed]
    except Exception as e:
        logger.error("Impossible de lire les données enregistrées (" + str(e) + ").")
        try:
            return [data_in[5], data_in[5], data_in[6], data_in[6]]
        except:
            return [100000, 100000, 100000, 100000]

#Enregistre les valeurs de tension de la batterie et du panneau solaire dans un fichier
def saveBatteryValues(bat_voltage):
    try:
        if not os.path.isfile(battery_file):
            open(battery_file, "w+").close()
        file = open(battery_file, "a+")
        file.write(str(calendar.timegm(time.gmtime())) + "," + str(bat_voltage) + "\n")
        file.close()
    except:
        logger.error("Impossible d'enregistrer les données de la batterie.")
        

