from configparser import ConfigParser
from loguru import logger


class ConfigFile:
    def __init__(self, filename):
        self.config = ConfigParser()
        self.filename = filename
        self.config.read(filename)
        self.subconfig = self.config['DEFAULT']

    def saveChange(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

    def setGsmPin(self, pin):
        self.subconfig['gsm_pin'] = pin

    def setBatteryLimit(self, limit):
        self.subconfig['seuil_alerte'] = limit

    def setGsmPswd(self, pswd):
        self.subconfig['gsm_password'] = pswd

    def setGsmMaster(self, num):
        self.subconfig['gsm_master'] = num

    def setWakeupHour(self, hour):
        self.subconfig['wakeup'] = hour
    
    def setSleepHour(self, hour):
        self.subconfig['sleep'] = hour

    def setSiteName(self, name):
        self.subconfig['nom'] = name

    def setSiteAltitude(self, altitude):
        self.subconfig['altitude'] = altitude

    def getGsmPin(self):
        return self.subconfig['gsm_pin']

    def getBatteryLimit(self):
        return self.subconfig.getfloat('seuil_alerte',11.5)

    def getGsmPswd(self):
        return self.subconfig.get('gsm_password','Kews')

    def getGsmMaster(self):
        return self.subconfig.get('gsm_master','+33780041476')

    def getWakeupHour(self, hour):
        return self.subconfig.getint('wakeup', 10)
    
    def getSleepHour(self, hour):
        return self.subconfig.getint('sleep', 18)

    def getSiteName(self, name):
        return self.subconfig.get("nom", 'Position inconnue')

    def getSiteAltitude(self, altitude):
        return self.subconfig.getint("altitude", 0)

    
gsm_power_gpio = 12
dht11_gpio =  23
cmd_tw_gpio = 29
ptt_gpio = 31
extinction_gpio = 22

tts_speed = 120
tts_pitch = 30

nuages_dewb = 237.7
nuages_dewa = 17.27
nuages_K = 122.7

mesures_nbtry = 5
mesures_nbmesures = 1

gsm_commands = ["batterie", "site", "nom", "debut", "début", "fin", "altitude", "logs", "data", "maitre", "maître"]

#Paramètres Sigfox


sigfox_addr = 0x55
pic_addr = 0x21


###REGISTRES DU PIC
#Registres liés à la date



logger.add("logs.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "LOG")
logger.add("data.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "DATA")
logger.add("battery.txt", rotation="1 days", level="INFO", format="{time:HH:mm:ss} {message}", filter=lambda record: record["extra"]["type"] == "BATTERY")


logger_log = logger.bind(type="LOG")
logger_data = logger.bind(type="DATA")
logger_battery = logger.bind(type="BATTERY")


def getNLogs(n):
    try:
        n = int(n)
        file = open("logs.txt", "r")
        line = list(filter(lambda l:len(l)>5, file.read().split("\n")))[-n]
        file.close()
        return line[:158]
    except:
       return "Erreur lors de la lecture des logs"

def getData():
    try:
        file = open("data.txt", "r")
        data = file.read()
        file.close()
        return data
    except:
        return "Erreur lors de la lecture des données"



def bcd2dec(bcd):
     return int(str(hex(bcd))[2:])



def isInt(i):
    try:
        int(i)
        return True
    except:
        return False

