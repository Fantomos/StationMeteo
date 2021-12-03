
## @file config.py
# Définition de la classe config. Elle permet la sauvegarde et récupération des paramètres importants de la station depuis un fichier de configuration.
##

from configparser import ConfigParser


## Classe ConfigFile. 
#  Cette classe permet d'extraire et de sauvegarder les données suivantes dans un dans un fichier de configuration sur la carte SD : 
#  numéro de téléphone maître, mot de passe maître, heure de réveil et de sommeil, nom et altitude de la station, seuil de batterie. 
#  Ainsi, même lorsque le Raspberry Pi est éteint, les données sont conservées.
#  Utilise la bibliothèque ConfigParser.
class ConfigFile:

    ## Constructeur. Prends en paramètre le nom du fichier de configuration.
    # @param filename Le nom du fichier de configuration.
    def __init__(self, filename):
        ## Objet ConfigParser.
        self.config = ConfigParser()
        ## Le nom du fichier de configuration.
        self.filename = filename
        ## Dictionnaire des paramètres du fichier de configuration.
        self.config.read(filename)
        ## Sous-dictionnaire des paramètres du fichier de configuration.
        self.subconfig = self.config['DEFAULT']
        

    ## Sauvegarde les changements dans le fichier de configuration.
    def saveChange(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)

    ## Modifie le code PIN de la carte SIM
    # @param pin Le nouveau code pin.
    def setGsmPin(self, pin):
        self.subconfig['gsm_pin'] = pin

    ## Modifie la tension de la batterie limite.
    # @param limit La nouvelle tension limite.
    def setBatteryLimit(self, limit):
        self.subconfig['seuil_alerte'] = limit

    ## Modifie le mot de passe maître de la station.
    # @param pswd Le nouveau mot de passe maître.
    def setGsmPswd(self, pswd):
        self.subconfig['gsm_password'] = pswd

    ## Modifie le numéro de téléphone maître de la station.
    # @param num Le nouveau numéro de téléphone maître.
    def setGsmMaster(self, num):
        self.subconfig['gsm_master'] = num

    ## Modifie l'heure de réveil de la station.
    # @param hour La nouvelle heure de réveil.
    def setWakeupHour(self, hour):
        self.subconfig['wakeup'] = hour
    
    ## Modifie l'heure d'extinction de la station.
    # @param hour La nouvelle heure d'extinction.
    def setSleepHour(self, hour):
        self.subconfig['sleep'] = round(hour)

    ## Modifie le nom de la station.
    # @param name La nouveau nom de la station.
    def setSiteName(self, name):
        self.subconfig['nom'] = name

    ## Modifie l'altitude de la station.
    # @param altitude La nouvelle altitude de la station.
    def setSiteAltitude(self, altitude):
        self.subconfig['altitude'] = altitude

    ## Recupère le code PIN de la carte SIM.
    # @return Retourne le PIN du GSM.
    def getGsmPin(self):
        return self.subconfig['gsm_pin']

    ## Recupère la tension de la batterie limite.
    # @return Retourne la tension limite de la batterie.
    def getBatteryLimit(self):
        return self.subconfig.getint('seuil_alerte',11500)

    ## Recupère le mot de passe maître de la station.
    # @return Retourne le mot de passe maître de la station.
    def getGsmPswd(self):
        return self.subconfig.get('gsm_password','Kews')

    ## Recupère le numéro de téléphone maître de la station.
    # @return Retourne le numéro de téléphone maître de la station.
    def getGsmMaster(self):
        return self.subconfig.get('gsm_master','+33780041476')

    ## Recupère l'heure de réveil de la station.
    # @return Retourne l'heure de réveil de la station.
    def getWakeupHour(self):
        return self.subconfig.getint('wakeup', 10)

    ## Recupère l'heure d'extinction de la station.
    # @return Retourne l'heure d'extinction de la station.
    def getSleepHour(self):
        return self.subconfig.getint('sleep', 18)

    ## Recupère le nom de la station.
    # @return Retourne le nom de la station.
    def getSiteName(self):
        return self.subconfig.get("nom", 'Position inconnue')

    ## Recupère l'altitude de la station.
    # @return Retourne l'altitude de la station.
    def getSiteAltitude(self):
        return self.subconfig.getint("altitude", 0)

