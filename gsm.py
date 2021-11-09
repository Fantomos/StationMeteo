import serial
import RPi.GPIO as GPIO
from time import sleep, mktime

## Classe Gsm.
# Cette classe permet la communication et la gestion du module GSM SIM800L via UART.
class Gsm:
    ## Constructeur.
    # @param gsm_power_gpio Numéro de pin pour allumer/éteindre le module GSM.
    # @param config Objet ConfigFile.
    # @param logger Logger principal.
    # @param mesures_nbtry Nombres d'essais maximum de l'initialisation des capteurs. La valeur par défaut est 5.
    # @param baudrate Baudrate du bus UART. La valeur par défaut est 115200.
    # @param timeout Timeout du bus UART. La valeur par défaut est 1.
    def __init__(self, gsm_power_gpio , config, logger, mesures_nbtry = 5, baudrate = 115200, timeout = 1):
        ##  Numéro de pin pour allumer/éteindre le module GSM.
        self.power_gpio = gsm_power_gpio
        ## Logger principal
        self.logger = logger
        ## Objet ConfigFile.
        self.config = config
        self.logger.info("Tentative d'ouverture du port série pour le module GSM...")
        for i in range(mesures_nbtry):
            try:
                ## Référence du bus UART.
                self.bus = serial.Serial("/dev/ttyAMA0", baudrate, timeout = timeout)
            except:
                logger.error("Impossible d'ouvrir le port série pour le module GSM.")
                self.bus = None
            else: #Si ça marche on sort de la boucle
                logger.success("Bus série avec le GSM ouvert")
                break
        
    ## Liste des commandes possible par SMS.
    command = ["batterie", "site", "nom", "debut", "début", "fin", "altitude", "logs", "data", "maitre", "maître"]

    ## Lit les données sur le bus série.
    # @return Retourne les données.
    def readBuffer(self):
        try:
            buffer = self.bus.read(1000).decode("8859")
            output = buffer
            while (len(buffer) > 0):
                sleep(0.2)
                buffer = self.bus.read(1000).decode("8859")
                output += buffer
            return output.strip()
        except:
            self.logger.error("Erreur lors de la lecture du buffer.")
            return ""

    ## Envoie une commande AT sans avoir besoin d'écrire "AT" .
    # @return Retourne la réponse à la commande.
    def sendAT(self, command):
        try:
            self.readBuffer()  #On vide le buffer avant
            sleep(0.2)
            self.bus.write(("AT" + command + "\r\n").encode("8859")) #On écrit la commande
            return self.readBuffer() #On renvoie la réponse
        except:
            self.logger.error("Erreur lors de l'envoi de la commande " + str(command) + ".")
            return "error"
            
    ## Envoie une impulsion de 2 sec sur le pin POWER du module GSM pour l'éteindre/allumer.
    def power(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.power_gpio, GPIO.OUT)
        GPIO.output(self.power_gpio, GPIO.HIGH)
        sleep(1)
        GPIO.output(self.power_gpio, GPIO.LOW)
        sleep(1)
        GPIO.setup(self.power_gpio, GPIO.IN)

    ## Allume le module GSM (power + commande vide) et renvoie le résultat d'une commande vide.
    # @return Retourne OK ou not OK si le module ne réponds pas.
    def turnOn(self):
        if self.sendAT("") != "OK":
            self.power()
            return "OK"
        else:
            return "not OK"

    ## Eteint la station
    def turnOff(self):
        if self.sendAT("") == "OK":
            self.power()

    ## Entre le code PIN de la carte SIM
    # @return Retourne la réponse à la commande.
    def enterPIN(self):
        return self.sendAT("+CPIN=\"0000\"")

    ## Initialise le module pour envoyer des SMS
    # @return Retourne la réponse aux commandes.
    def setupSMS(self):
        output = self.sendAT("+CMGF=1") #Met en mode texte
        output += self.sendAT("+CSCS=\"GSM\"") #Indique un encodage GSM
        self.sendAT("+CPMS=\"SM\"") #Indique que le stockage se fait dans la carte SIM
        return output

    ## Envoie un seul SMS au numéro indiqué.
    # @param numero Le numéro de téléphone auquel envoyer un SMS.
    # @param txt Le message à envoyer.
    # @return Retourne la réponse aux commandes.
    def sendSingleSMS(self, numero, txt):
        output = self.sendAT("+CMGS=\"" + numero + "\"") #On envoie le numéro
        output += self.sendAT(txt[:159]) #On envoie le texte du SMS
        output += self.sendAT("\x1A") #On envoie le caractère de fin
        sleep(0.1)
        self.readBuffer() #On vide le buffer
        return output

    ## Envoie autant de SMS que nécessaire au numéro indiqué pour envoyer le texte indiqué.
    # @param numero Le numéro de téléphone auquel envoyer un SMS.
    # @param txt Le message à envoyer.
    # @return Retourne la réponse aux commandes.
    def sendSMS(self, numero, txt):
        output = []
        sms_list = [txt[150*i:150*(i+1)] for i in range(1+len(txt) // 150)] #On découpe le texte en morceau d'au plus 150 caractères de long
        for i in range(len(sms_list)): #On envoie chaque morceau
            output.append(self.sendSingleSMS(numero, sms_list[i]))
            if i < len(sms_list) - 1: #Si ce n'est pas le dernier morceau, on attend avant le prochain
                sleep(1.5)
        self.readBuffer()
        return ",".join(output)

    ## Renvoie la date sous la forme d'un tableau [année, mois, jour, heure, minute, seconde].
    # @return Retourne le timestamp UNIX représentant le temps actuel ou 0 en cas d'erreur lors de l'accés au module.
    def getDateTime(self):
        self.logger.info("Tentative d'actualiser l'heure depuis le module GSM...")
        buffer = self.sendAT("+CCLK?") #On récupère la date et heure du module GSM
        if len(buffer) > 17: #Si on a bien tout reçu, on le renvoie, sinon on renvoie un tableau vide
            datetime = buffer.split("\"")[1]
            date = datetime.split(",")[0].split("/")
            clock = datetime.split(",")[1].split("+")[0].split(":")
            date[2] = "20" + date[2]
            return mktime((int(date[2]), int(date[1]), int(date[0]), int(clock[0]), int(clock[1]), int(clock[2]), 0, 0, -1))
        else:
            self.logger.error("Impossible d'obtenir la date et heure depuis le module GSM")
            return 0
        
    ## Renvoie le nombre de SMS dans la mémoire de la carte. On reçoit une réponse sous la forme "+CPMS: x,y,x,y,x,y", où x est le nombre de message stocké et y la capacité.
    # @return Retourne le nombre de SMS ou -1 en cas d'erreur.
    def getSMSCount(self):
        buffer = self.sendAT("+CPMS=\"SM\"")
        try:
            return int(buffer[7:].split(",")[0])
        except:
            return -1
        
    ## Renvoie les indices des SMS enregistrés (nombre entre 1 et 50]
    # @return Retourne la listes des indices des SMS enregistrés.
    def getSMSIndexes(self):
        buffer = self.sendAT("+CMGL=\"ALL\"").split("\r\n")
        indexes = []
        for data in buffer:
            if data.startswith("+CMGL"):
                try:
                    index = data[7:].split(",")[0]
                    if not index in indexes:
                        indexes.append(index)
                except:
                    self.logger.error("Erreur dans la récupération des index")
        return indexes

    ## Lit un SMS à partir de l'indice donné et renvoie le texte du message et le numéro de l'expéditeur.
    # @param index L'indice du SMS à lire.
    # @return Retourne le message et le numéro de téléphone de l'expéditeur ou un tableau vide en cas d'erreur lors de la lecture.
    def readSMS(self, index):
        self.readBuffer()
        buffer = self.sendAT("+CMGR=" + str(index)) #On demande le SMS
        data = buffer.split("\r\n")
        sleep(0.1)
        try:
            number = data[0].split(",")[1].strip("\"")
            body = data[1]
            return [convertToAscii(body), number]
        except:
            self.logger.error("Erreur lors de la lecture du SMS d'indice " + str(index))
            return []

    ## Supprime un SMS à partir de son indice.
    # @param index L'indice du SMS à supprimer.
    # @return Retourne la réponse à la commande.
    def deleteSMS(self, index):
        sleep(0.1)
        return self.sendAT("+CMGD=" + str(index) + ",0")

    ## Supprime tous les SMS.
    # @return Retourne la réponse à la commande.
    def deleteAllSMS(self):
        sleep(0.1)
        self.readBuffer()
        return self.sendAT("+CMGD=0,4")

    ## Renvoie le status d'un SMS.
    # @param sms Le SMS dont l'on souhaite obtenir le status.
    # @return Retourne le status du SMS. -1 = SMS vide. 0 = SMS normal (dans tous les cas sauf ceux ci-dessous). 1 = commande pour modifier un paramètre (si le texte contient "=" et une commande valide). 2 = commande pour lire un paramètre (si le texte contient "?" et une commande valide). 3 = mot de passe reçu (si le texte contient le mot de passe). 
    def getStatus(self ,sms):
        if len(sms) > 1:
            sms = sms[0]
            if ("=" in sms and sms.split("=")[0].lower().strip() in self.command):
                return 1
            elif ("?" in sms and sms.split("?")[0].lower().strip() in self.command):
                return 2
            elif (self.config.getGsmPswd() in sms):
                return 3
            else:
                return 0
        else:
            return -1

    ## Exécute une commande de lecture de paramètre à partir du texte du sms.
    # @param command La commande à exécuter.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    # @return Retourne la réponse à la commande.
    def executeGetCommand(self, command, sensorsData):
        #On récupère ce qui est avant le ?, on le met en minuscule et on enlève les espaces avant et après
        word = command.split("?")[0].lower().strip()
        print("command : " + word)
        #Selon la commande, on effectue différentes actions
        if word == "batterie":
            return str(sensorsData["battery"]) + " V"
        elif word == "site" or word == "nom":
            return "Site : \n" + self.config.getSiteName()
        elif word == "debut" or word == "début":
            return "Heure d'éveil de la station : " + self.config.getWakeupHour() + " h"
        elif word == "fin":
            return "Heure d'extinction de la station : " + self.config.getSleepHour() + " h"
        elif word == "altitude":
            return "Altitude de la station : " + self.config.getSiteAltitude() + " m"
        elif word == "logs":
            return self.config.getNLogs(command.split("?")[1].strip() if command.split("?")[1].strip().isnumeric() else 1)
        elif word == "data":
            return self.config.getData() #TODO
        elif word == "maitre" or word == "maître":
            return "Numéro maître de la station :\n" + self.config.getGsmMaster()
        
        return "Commande inconnue."

    ## Exécute une commande de modification de paramètres à partir d'un sms, et renvoie la réponse.
    # @param command La commande à exécuter.
    # @return Retourne la réponse à la commande.
    def executeSetCommand(self, command):
        #On récupère ce qui est de part et d'autres du =, on met le premier en minuscule et on enlève les espaces avant et après
        word = command.split("=")[0].lower().strip()
        arg = command.split("=")[1].strip()
        #Selon la commande, on effectue différentes actions
        if word == "debut" or word == "début":
            result = self.config.setWakeupHour(arg)
            if result:
                return "Heure d'éveil correctement mise à jour : \n" + str(arg) + " h"
            else:
                return "Heure d'éveil incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
        elif word == "fin":
            result = self.config.setSleepHour(arg)
            if result:
                return "Heure d'extinction correctement mise à jour : \n" + str(arg) + " h"
            else:
                return "Heure d'extinction incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
        elif word == "site" or word == "nom":
            result = self.config.setSiteName(arg)
            if result:
                return "Site correctement mis à jour : \n\"" + str(arg[:125]) + "\""
            else:
                return "Une erreur est survenue, merci de réessayer."
        elif word == "altitude":
            result = self.config.setSiteAltitude(arg)
            if result:
                return "Altitude correctement mise à jour : \n" + str(arg) + " m"
            else:
                return "Altitude incorrecte, merci de n'envoyer qu'un nombre."
        
        return "Commande inconnue."

    ## Répond à tous les SMS reçus.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    def respondToSMS(self, sensorsData):
        self.logger.info("Analyse des SMS reçus...")
        if self.getSMSCount() > 0: #Si on a reçu des SMS
            indexes = self.getSMSIndexes() #On récupère la liste des indices des SMS
            self.logger.success(str(len(indexes)) + " SMS reçus")
            for index in indexes[:20]: #On les parcourt
                self.logger.info("Traitement du SMS numéro" + str(index) + "...")
                sms = self.readSMS(index) #On lit le sms (format [message, numéro])
                print(index, sms)
                status = self.getStatus(sms) #On récupère le status (commande, mot de passe, infos)
                if status == 1: #S'il s'agit d'une commande d'écriture
                    if (sms[1] == self.config.getGsmMaster()): #Si le numéro est le bon, on l'autorise
                        self.sendSMS(sms[1], self.executeSetCommand(sms[0])) #On exécute la commande et on réponds le message de confirmation ou d'erreur
                    else: #Sinon, on répond que ce n'est pas possible
                        self.sendSMS(sms[1], "Vous n'avez pas la permission d'effectuer cette commande.")
                elif status == 2: #S'il s'agit d'une commande de lecture, on renvoie la réponse adaptée
                    self.sendSMS(sms[1], self.executeGetCommand(sms[0]), sensorsData)
                elif status == 3: #S'il s'agit du mot de passe
                    self.sendSMS(sms[1], "Vous etes désormais le nouveau responsable de la station.")
                    self.config.setGsmMaster(sms[1])
                elif status == 0: #Si ce n'est pas une des 3 possibilités, on renvoie le sms contenant les infos
                    self.sendSMS(sms[1], self.createSMS(sensorsData))
                self.logger.success("Traitement du SMS numéro" + str(index) + "terminé")
                sleep(0.1)
            #On supprime tous les SMS
            try:
                self.deleteAllSMS()
            except:
                self.logger.error("Erreur lors de la suppression des SMS")
            else:
                self.logger.success("Suppression des SMS terminée")
            sleep(3)
        
        #On mesure la tension de la batterie, et s'il elle sous le seuil d'alerte, on envoie un message
        battery = sensorsData['Battery']
        if battery <= self.config.getBatteryLimit():
            self.sendSMS(self.config.getGsmMaster(), "[" +  sensorsData['Time'] + "]\n/!\\ La tension de la batterie est faible (" + str(battery) + " V), la station risque de ne plus fonctionner correctement. /!\\")



    ## Crée le message à envoyer par SMS pour transmettre les informations. Pour chaque valeur, on écrit "n/a" si la valeur n'a pas été trouvée.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    # @return Retourne le message.
    def createSMS(self, sensorsData):
        temperature = str(round(sensorsData['Temperature'], 1)) if float(sensorsData['Temperature']) != 0 else "n/a"
        vitesse_moy = str(int(sensorsData['Speed']))
        vitesse_max = str(int(sensorsData['Speed_max']))
        direction_moy = sensorsData['Direction']
        direction_max = sensorsData['DIrection_max']
        pression = str(int(sensorsData['Pressure'])) if int(sensorsData['Pressure']) != 0 else "n/a"
        humidite = str(int(sensorsData['Humidity'])) if int(sensorsData['Humidity']) != 0 else "n/a"
        hauteur_nuages = str(int(sensorsData['Cloud'])) if int(sensorsData['Cloud']) != 0 else "n/a"
        
        output = "[" + str(sensorsData['Time']) + "]\n"
        output += "Temp: " + temperature + " C\n"
        output += "Vent moy: " + vitesse_moy + "km/h " + direction_moy + "° \n"
        output += "Vent max: " + vitesse_max + "km/h " + direction_max + "° \n"
        output += "Humi: " + humidite + "%\n"
        output += "Press: " + pression + "hPa\n"
        output += "Haut nuages: " + hauteur_nuages + "m"
        #On ajoute le nom du site et on coupe à 158 caractères pour éviter d'envoyer 2 SMS
        if len(output) < 158:
            output = (self.config.getSiteName() + " (" + self.config.getSiteAltitude() + " m)")[:157-len(output)] + "\n" + output
        else:
            output = output[:158]
        return output

## Convertis le message en ASCII.
# @param body Le message à convertir.
# @return Retourne le code ASCII ou le message en cas d'erreur.
def convertToAscii(body):
        try:
            letters = body[::4]
            output = ""
            for letter in letters:
                if len(letter) == 4 and sum([c in "0123456798ABCDEF" for c in letter]) == 4 and letter[0] == "0":
                    output += chr(int(letter, 16))
                else:
                    return body
            return output
        except:
            return body