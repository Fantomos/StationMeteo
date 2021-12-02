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
                self.logger.info("Configuration du module GSM...")
                self.setup()
            except Exception as e:
                self.logger.error(e)
                logger.error("Impossible d'ouvrir le port série ou de configurer le module GSM.")
                self.bus = None
            else: #Si ça marche on sort de la boucle
                logger.success("Module GSM configuré")
                break
        
    ## Liste des commandes possible par SMS.
    command = ["batterie", "site", "nom", "debut", "début", "eveil" , "éveil","fin", "extinction","altitude", "logs", "data", "maitre", "maître","aide"]

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
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Erreur lors de la lecture du buffer.")
            return ""

    ## Envoie une commande AT sans avoir besoin d'écrire "AT" .
    # @return Retourne la réponse à la commande.
    def sendAT(self, command):
        try:
            self.readBuffer()  #On vide le buffer avant
            self.bus.write(("AT" + command + "\r\n").encode("8859")) #On écrit la commande
            return self.readBuffer() #On renvoie la réponse
        except Exception as e:
            self.logger.error(e)
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

    ## Initialise le module pour se connecter au réseau et envoyer des SMS
    # @return Retourne la réponse aux commandes.
    def setup(self):
        output = self.sendAT("+CPIN=\"0000\"") + "\n"
        output += self.sendAT("+CLTS=1") + "\n" # Active la synchronisation de l'heure par le réseaux
        output += self.sendAT("+CMGF=1") + "\n" # Met en mode texte
        output += self.sendAT("+CSCS=\"GSM\"") + "\n" # Indique un encodage GSM
        output += self.sendAT("+CPMS=\"SM\",\"SM\",\"SM\"") + "\n" # Indique que le stockage se fait dans la carte SIM
        output += self.sendAT("&W") # Sauvegarde la configuration sur la ROM du module
        return output

    ## Envoie un SMS au numéro indiqué.
    # @param numero Le numéro de téléphone auquel envoyer un SMS.
    # @param txt Le message à envoyer.
    # @return Retourne la réponse aux commandes.
    def sendSMS(self, numero, txt):
        output = self.sendAT("+CMGS=\"" + numero + "\"\r" + txt) + "\n" #On envoie le numéro
        self.bus.write(bytes([26]))
        self.readBuffer() #On vide le buffer
        return output

    ## Renvoie la date sous la forme d'un tableau [année, mois, jour, heure, minute, seconde].
    # @return Retourne le timestamp UNIX représentant le temps actuel ou 0 en cas d'erreur lors de l'accés au module.
    def getDateTime(self):
        self.logger.info("Tentative d'actualiser l'heure depuis le module GSM...")
        buffer = self.sendAT("+CCLK?") #On récupère la date et heure du module GSM
        if len(buffer) > 17: #Si on a bien tout reçu, on le renvoie, sinon on renvoie un tableau vide
            datetime = buffer.split("\"")[1]
            date = datetime.split(",")[0].split("/")
            clock = datetime.split(",")[1].split("+")[0].split(":")
            date[0] = "20" + date[0]
            return round(mktime((int(date[0]), int(date[1]), int(date[2]), int(clock[0]), int(clock[1]), int(clock[2]), 0, 0, -1)))
        else:
            self.logger.error("Impossible d'obtenir la date et heure depuis le module GSM")
            return 0
        
    ## Renvoie les indices des SMS enregistrés (nombre entre 1 et 50)
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
                except Exception as E:
                    self.logger.error(E)
                    self.logger.error("Erreur dans la récupération des index")
        return indexes

    ## Lit un SMS à partir de l'indice donné et renvoie le texte du message et le numéro de l'expéditeur.
    # @param index L'indice du SMS à lire.
    # @return Retourne le message et le numéro de téléphone de l'expéditeur ou un tableau vide en cas d'erreur lors de la lecture.
    def readSMS(self, index):
        self.readBuffer()
        buffer = self.sendAT("+CMGR=" + str(index)) # On demande la lecture du SMS
        try:
            number = buffer.split(",")[1].strip("\"") # On parse la réponse
            text = buffer.split("\r\n")[2]
            return [text, number]
        except Exception as E:
            self.logger.error(E)
            self.logger.error("Erreur lors de la lecture du SMS d'indice " + str(index))
            return []

    ## Supprime un SMS à partir de son indice.
    # @param index L'indice du SMS à supprimer.
    # @return Retourne la réponse à la commande.
    def deleteSMS(self, index):
        return self.sendAT("+CMGD=" + str(index) + ",0")

    ## Supprime tous les SMS.
    # @return Retourne la réponse à la commande.
    def deleteAllSMS(self):
        self.readBuffer()
        return self.sendAT("+CMGD=1,4")

    ## Renvoie le status d'un SMS.
    # @param sms Le SMS dont l'on souhaite obtenir le status.
    # @return Retourne le status du SMS. 0 = SMS normal (dans tous les cas sauf ceux ci-dessous). 1 = commande pour modifier un paramètre (si le texte contient "=" et une commande valide). 2 = commande pour lire un paramètre (si le texte contient "?" et une commande valide). 3 = mot de passe reçu (si le texte contient le mot de passe). 
    def getStatus(self ,sms):
        if ("=" in sms and sms.split("=")[0].lower().strip() in self.command):
            return 1
        elif ("?" in sms and sms.split("?")[0].lower().strip() in self.command):
            return 2
        elif (self.config.getGsmPswd() in sms):
            return 3
        else:
            return 0


    ## Exécute une commande de lecture de paramètre à partir du texte du sms.
    # @param command La commande à exécuter.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    # @return Retourne la réponse à la commande.
    def executeGetCommand(self, command, sensorsData):
        #On récupère ce qui est avant le ?, on le met en minuscule et on enlève les espaces avant et après
        word = command.split("?")[0].lower().strip()

        #Selon la commande, on effectue différentes actions
        if word == "batterie":
            self.logger.info("Envoi de la tension de la batterie")
            return "Tension de la batterie : " + str(sensorsData["Battery"]) + " mV"
        elif word == "site" or word == "nom":
            self.logger.info("Envoi du nom de la station")
            return "Nom de la station : " + str(self.config.getSiteName())
        elif word == "debut" or word == "début" or word == "eveil" or word == "éveil":
            self.logger.info("Envoi de l'heure d'éveil de la station")
            return "Heure d'éveil de la station : " + str(self.config.getWakeupHour()) + " h"
        elif word == "fin" or word == "extinction":
            self.logger.info("Envoi de l'heure d'extinction de la station")
            return "Heure d'extinction de la station : " + str(self.config.getSleepHour()) + " h"
        elif word == "altitude":
            self.logger.info("Envoi de l'altitude de la station")
            return "Altitude de la station : " + str(self.config.getSiteAltitude()) + " m"
        elif word == "logs":
            self.logger.info("Envoi des logs")
            return self.config.getNLogs(command.split("?")[1].strip() if command.split("?")[1].strip().isnumeric() else 1)
        elif word == "data":
            self.logger.info("Envoi des N dernières données")
            return self.config.getData() #TODO
        elif word == "aide":
            self.logger.info("Envoi de la liste des commandes")
            return "Envoyez n'importe quel message pour obtenir le dernier bulletin météo. \nVotre sms peut aussi contenir l'une des commandes suivantes : batterie?, nom?, altitude?, eveil?, extinction?, maitre?"
        elif word == "maitre" or word == "maître":
            self.logger.info("Envoi du numéro maître de la station")
            return "Numéro maitre de la station : " + str(self.config.getGsmMaster())
        
        self.logger.info("Commande inconnue")
        return "Commande inconnue."

    ## Exécute une commande de modification de paramètres à partir d'un sms, et renvoie la réponse.
    # @param command La commande à exécuter.
    # @return Retourne la réponse à la commande.
    def executeSetCommand(self, command):
        #On récupère ce qui est de part et d'autres du =, on met le premier en minuscule et on enlève les espaces avant et après
        word = command.split("=")[0].lower().strip()
        arg = command.split("=")[1].strip()
        #Selon la commande, on effectue différentes actions
        if word == "debut" or word == "début" or word == "eveil" or word == "éveil":
            try:
                self.config.setWakeupHour(str(int(arg)))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'heure de réveil")
                return "Heure de réveil incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
            else:
                self.logger.success("L'heure de réveil a été correctement mise à jour : " + str(arg) + "h")
                return "Heure de réveil correctement mise a jour : " + str(arg) + " h"

        elif word == "fin" or word == "extinction":
            try:
                self.config.setSleepHour(str(int(arg)))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'heure d'extinction")
                return "Heure d'extinction incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
            else:
                self.logger.success("L'heure d'extinction a été correctement mise à jour : " + str(arg) + "h")
                return "Heure d'extinction correctement mise a jour : " + str(arg) + "h"

        elif word == "site" or word == "nom":
            try:
                self.config.setSiteName(str(arg[:125]))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour le nom de la station")
                return "Une erreur est survenue, merci de réessayer."
            else:
                self.logger.success("Le nom de la station a été correctement mise à jour : " + str(arg[:125]))
                return "Le nom de la station a été correctement mis a jour : " + str(arg[:125])

        elif word == "altitude":
            try:
                self.config.setSiteAltitude(str(int(arg)))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'altitude")
                return "Altitude incorrecte, merci de n'envoyer qu'un nombre."
            else:
                self.logger.success("L'altitude a été correctement mis à jour : " + str(arg))
                return "Altitude correctement mise a jour : " + str(arg) + " m"
        
        self.logger.info("Commande inconnue")
        return "Commande inconnue."

    ## Répond à tous les SMS reçus.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    def respondToSMS(self, sensorsData):
        config_set = False
        self.logger.info("Analyse des SMS reçus...")
        indexes = self.getSMSIndexes() #On récupère la liste des indices des SMS
        self.logger.success(str(len(indexes)) + " SMS reçus")
        if len(indexes) > 0: #Si on a bien reçu des SMS
            for index in indexes[:20]: #On les parcourt
                self.logger.info("Traitement du SMS numéro " + str(index) + "...")
                try:
                    sms = self.readSMS(index) #On lit le sms (format [message, numéro])
                    self.logger.info("Lecture du SMS : " + str(sms[1]) + " | Message : " + str(sms[0]))
                    status = self.getStatus(sms[0]) #On récupère le status (commande, mot de passe, infos)
                    if status == 1: #S'il s'agit d'une commande d'écriture
                        if (sms[1] == self.config.getGsmMaster()): #Si le numéro est le bon, on l'autorise
                            self.sendSMS(sms[1], self.executeSetCommand(sms[0])) #On exécute la commande et on réponds le message de confirmation ou d'erreur
                            config_set = True
                        else: #Sinon, on répond que ce n'est pas possible
                            self.logger.info("Permission refusée : ce numéro n'est pas le maître de la station")
                            self.sendSMS(sms[1], "Vous n'avez pas la permission d'effectuer cette commande.")
                    elif status == 2: #S'il s'agit d'une commande de lecture, on renvoie la réponse adaptée
                        self.sendSMS(sms[1], self.executeGetCommand(sms[0], sensorsData))
                    elif status == 3: #S'il s'agit du mot de passe
                        self.sendSMS(sms[1], "Vous etes désormais le nouveau responsable de la station.")
                        self.config.setGsmMaster(str(sms[1]))
                        config_set = True
                        self.logger.info("Nouveau maître de la station : " + str(sms[1]))
                    elif status == 0: #Si ce n'est pas une des 3 possibilités, on renvoie le sms contenant les infos
                        self.sendSMS(sms[1], self.createSMS(sensorsData))
                        self.logger.info("Envoie du rapport météo")
                except Exception as e:
                    self.logger.error(e)
                    self.logger.error("Impossible de traiter le SMS numéro "+ str(index))
                else :
                    self.logger.success("Traitement du SMS numéro " + str(index) + " terminé")
                sleep(5)
           
            if config_set :
                try:
                    self.config.saveChange()
                except Exception as e:
                    self.logger.error(e)
                    self.logger.error("Impossible d'écrire sur le fichier de configuration")
                else:
                    self.logger.success("Fichier de configuration mis à jour")

               

            try:  #On supprime tous les SMS
                self.deleteAllSMS()
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Erreur lors de la suppression des SMS")
            else:
                self.logger.success("Suppression des SMS terminée")
        
        #On mesure la tension de la batterie, et s'il elle sous le seuil d'alerte, on envoie un message
        battery = sensorsData['Battery']
        if battery <= self.config.getBatteryLimit():
            self.sendSMS(self.config.getGsmMaster(), "[" +  sensorsData['Time'] + "]\n/!\\ La tension de la batterie est faible (" + str(battery) + " V), la station risque de ne plus fonctionner correctement. /!\\")



    ## Crée le message à envoyer par SMS pour transmettre les informations. Pour chaque valeur, on écrit "n/a" si la valeur n'a pas été trouvée.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    # @return Retourne le message.
    def createSMS(self, sensorsData):
        temperature = str(round(sensorsData['Temperature'], 1)) if float(sensorsData['Temperature']) < 100 and float(sensorsData['Temperature']) > -50 else "n/a"
        vitesse_moy = str(int(sensorsData['Speed'])) if float(sensorsData['Speed']) < 300 and float(sensorsData['Speed']) >= 0 else "erreur"
        vitesse_max = str(int(sensorsData['Speed_max'])) if float(sensorsData['Speed_max']) < 300 and float(sensorsData['Speed_max']) >= 0 else "erreur"
        direction_moy = str(sensorsData['Direction'])  if float(sensorsData['Direction']) < 360 and float(sensorsData['Direction']) >= 0 else "erreur"
        direction_max = str(sensorsData['Direction_max']) if float(sensorsData['Direction_max']) < 360 and float(sensorsData['Direction_max']) >= 0 else "erreur"
        pression = str(int(sensorsData['Pressure'])) if int(sensorsData['Pressure']) > 400 and int(sensorsData['Pressure']) < 1500 else "n/a"
        humidite = str(int(sensorsData['Humidity'])) if int(sensorsData['Humidity']) <= 100 and int(sensorsData['Humidity']) >= 0 else "n/a"
        hauteur_nuages = str(int(sensorsData['Cloud'])) if int(sensorsData['Cloud']) >= 0 else "n/a"
        
        output = (self.config.getSiteName() + " (" + str(self.config.getSiteAltitude()) + " m)") + "\n"
        output += "[" + str(sensorsData['Time']) + "]\n"
        output += "Température : " + temperature + " C\n"
        output += "Vent moyen : " + vitesse_moy + " km/h " + direction_moy + "\xB0 \n"
        output += "Vent maximum : " + vitesse_max + " km/h " + direction_max + "\xB0 \n"
        output += "Humidité : " + humidite + " %\n"
        output += "Pression : " + pression + " hPa\n"
        output += "Hauteur des nuages: " + hauteur_nuages + " m"

        return output
