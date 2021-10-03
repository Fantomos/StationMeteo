from time import sleep
from smbus2 import SMBus

class I2C:
    def __init__(self, logger, mesures_nbtry = 5):
        for i in range(mesures_nbtry):
            try:
                self.i2cbus = SMBus(1) #On tente d'établir la connexion
            except: #Si ça ne marche pas on attend avant de rententer
                logger.error("Impossible de se connecter au bus I2C, essai " + str(i) + "/" + str(mesures_nbtry) + ".")
                sleep(1)
            else: #Si ça marche on sort de la boucle
                logger.success("Bus I2C connecté")
                break





class Pic:
    def __init__(self, i2cbus, logger, i2c_address = 0x21):
        self.i2cbus = i2cbus
        self.i2c_address = i2c_address
        self.logger = logger
        self.register =	{
            "year" : 0x0,
            "month" : 0x1,
            "wd" : 0x2,
            "day" : 0x3,
            "hour" : 0x4,
            "min" : 0x5,
            "sec" : 0x6,

            #Registres liés à l'alarme
            "alarm_month" : 0x7,
            "alarm_wd" : 0x8,
            "alarm_day" : 0x9,
            "alarm_hour" : 0xA,
            "alarm_min" : 0xB,
            "alarm_sec" : 0xC,
            "alarm_con" : 0xD,
            "alarm_rtccal" : 0xE,
            "alarm_rpt" : 0xF,

            #Registres de stockage d'information
            "vb0gpr" : 0x10,
            "vb1gpr" : 0x11,
            "vb2gpr" : 0x12,
            "vb3gpr" : 0x13,

            #Registres liés à la mesure du vent
            "wind_dir" : 0x14,
            "wind_speed_h" : 0x15,
            "wind_speed_l" : 0x16,

            #Autres
            "state" : 0x17, #Permet de savoir si le PIC a fini ses mesures
            "battery" : 0x18, #Permet de récupérer la tension de la batterie

            #PIC VALEURS
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "alarm_min_val" : 0x00,
            "alarm_sec_val" : 0x45
        }
   

    #Fonction permettant de lire la valeur d'un registre du PIC. Renvoie 100000 en cas d'erreur.
    def readPicReg(self, regName):
        sleep(0.05) #Délai sinon ça marche pas
        try:
            self.i2cbus.write_byte(self.i2c_address, self.register[regName])  #On envoie d'abord l'adresse du registre
            return self.i2cbus.read_byte(self.i2c_address) #On lit ensuite la valeur qui arrive
        except:
            self.logger.error("Impossible de lire le registre " + regName + "(" +  str(self.register[regName]) + ") sur le PIC.")
            return 100000

    #Ecrit une valeur donnée (data) dans un registre donné (reg)
    def writePicReg(self, regName, data):
        try:
            self.i2cbus.write_byte_data(self.i2c_address, self.register[regName], data)
        except:
            self.logger.error("Impossible d'envoyer les données au PIC sur le registre " + regName + "(" +  str(self.register[regName]) + "), données=" + str(data) + ").")

    #Envoie la date et l'heure reçus depuis le GSM au PIC au format [année, mois, jour, heure, minute, seconde]
    def setDateTime(self, dt):
        if len(dt) == 6: #Si on les a récupérés correctement
            datetime = [dec2bcd(int(i)) for i in dt] #On les convertit en BCD et on les envoie
            self.writePicReg("year", datetime[0])
            self.writePicReg("month", datetime[1])
            self.writePicReg("wd", 0)
            self.writePicReg("day", datetime[2])
            self.writePicReg("hour", datetime[3])
            self.writePicReg("min", datetime[4])
            self.writePicReg("sec", datetime[5])
        return dt

    def resetWatchdogTimer(self):
        self.readPicReg("year")

    #Permet de lire toutes les données du PIC concernant le vent. Renvoie 100000 en cas d'erreur.
    def readPicData(self):
        try:
            while self.readPicReg("state") != 1: #Tant que le PIC n'a pas fini ses mesures on attend
                sleep(0.5)
            
            direction_vent = self.readPicReg("wind_dir") #On lit la direction du vent (entre 0 et 15)
            windSpeed_h = self.readPicReg("wind_speed_h")    #On lit l'octet de poids fort de la vitesse du vent
            windSpeed_l = self.readPicReg("wind_speed_l")   #On lit l'octet de poids faible de la vitesse du vent
            if windSpeed_h == 100000 or windSpeed_l == 100000: #Si la lecture de la vitesse a eu un problème, on renvoie 100000
                return direction_vent, 100000
            else:
                return direction_vent, (windSpeed_h * 256 + windSpeed_l) / 10
        except:
            self.logger.error("Impossible de lire les données du PIC.")
            return 100000, 100000



def dec2bcd(dec):
    return int("0x" + str(dec), 16)