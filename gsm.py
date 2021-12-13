
## @file gsm.py
# Définition de la classe gsm. Elle permet la communication avec le module GSM SIM800L.
##
from time import sleep, mktime, time
from loguru import logger

## Classe Gsm.
# Cette classe permet la communication et la gestion du module GSM SIM800L via UART.
class Gsm:
    ## Constructeur.
    # @param config Objet ConfigFile.
    # @param pi Instance de pigpio.
    # @param logger Logger principal.
    # @param mesures_nbtry Nombres d'essais maximum de l'initialisation des capteurs. La valeur par défaut est 5.
    # @param baudrate Baudrate du bus UART. La valeur par défaut est 115200.
    # @param timeout Timeout du bus UART. La valeur par défaut est 1.
    def __init__(self, config, pi, logger, mesures_nbtry = 5, baudrate = 115200, timeout = 1):
        ## Logger principal
        self.logger = logger
        ## Instance de pigpio
        self.pi = pi
        ## Objet ConfigFile.
        self.config = config
        self.logger.info("Tentative d'ouverture du port série pour le module GSM...")
        for i in range(mesures_nbtry):
            try:
                ## Référence du bus UART.
                self.handle = pi.serial_open("/dev/ttyAMA0", baudrate)
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible d'ouvrir le port série ou de configurer le module GSM.")
                self.handle = None
            else: #Si ça marche on sort de la boucle
                self.logger.success("Port série ouvert")
                break
        
    ## Liste des commandes possible par SMS.
    command = ["batterie", "seuil","site", "nom", "debut", "début", "eveil" , "éveil","reveil" , "réveil","fin", "extinction","altitude", "logs", "data", "maitre", "maître","aide"]

    ## Lit les données sur le bus série.
    # @return Retourne les données.
    def readBuffer(self, wait = 0.1):
        try:
            sleep(wait)
            rdy = self.pi.serial_data_available(self.handle)
            start = time()
            while rdy == 0:
                if time() - start > 10:
                    raise Exception("Timeout : Aucune réponse")
                rdy = self.pi.serial_data_available(self.handle)
                sleep(0.001)
            (b, d) = self.pi.serial_read(self.handle, rdy)
            return d.decode("8859")
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Erreur lors de la lecture du buffer.")
            return "Erreur"

    ## Envoie une commande AT sans avoir besoin d'écrire "AT" .
    # @return Retourne la réponse à la commande.
    def sendAT(self, command, wait = 0.1):
        try:
            self.pi.serial_write(self.handle,("AT" + command + "\r").encode("8859")) #On écrit la commande
            return self.readBuffer(wait) #On renvoie la réponse
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Erreur lors de l'envoi de la commande " + str(command) + ".")
            return "error"

    ## Initialise le module pour se connecter au réseau et envoyer des SMS
    # @return Retourne la réponse aux commandes.
    def setup(self):
        self.logger.info("Configuration du module GSM...")
        output = self.sendAT("E0")
        output += self.sendAT("+CLTS=1") # Active la synchronisation de l'heure par le réseaux
        output += self.sendAT("+CMGF=1") # Met en mode texte
        output += self.sendAT("+CSCS=\"GSM\"")# Indique un encodage GSM
        output += self.sendAT("+CPMS=\"SM\",\"SM\",\"SM\"") # Indique que le stockage se fait dans la carte SIM
        output += self.sendAT("&W") # Sauvegarde la configuration sur la ROM du module
        self.logger.success("Module GSM configuré")
        return output

    ## Configure le module GSM en sommeil profond
    # @return Retourne la réponse aux commandes.
    def sleep(self):
        return self.sendAT("+CSCLK=2")

    ## Envoie un SMS au numéro indiqué.
    # @param numero Le numéro de téléphone auquel envoyer un SMS.
    # @param txt Le message à envoyer.
    # @return Retourne la réponse aux commandes.
    def sendSMS(self, numero, txt):
        output = self.sendAT("+CMGS=\"" + numero + "\"\r") #On envoie le numéro
        self.pi.serial_write(self.handle, (txt + chr(26)).encode("8859"))
        output += self.readBuffer(1)
        return output

    ## Renvoie la date sous la forme d'un tableau [année, mois, jour, heure, minute, seconde].
    # @return Retourne le timestamp UNIX représentant le temps actuel ou 0 en cas d'erreur lors de l'accés au module.
    def getDateTime(self):
        self.logger.info("Tentative d'actualiser l'heure depuis le module GSM...")
        buffer = self.sendAT("+CCLK?",0.1) #On récupère la date et heure du module GSM
        try:
            print(buffer)
            datetime = buffer.split("\"")[1]
            date = datetime.split(",")[0].split("/")
            clock = datetime.split(",")[1].split("+")[0].split(":")
            date[0] = "20" + date[0]
            return round(mktime((int(date[0]), int(date[1]), int(date[2]), int(clock[0]), int(clock[1]), int(clock[2]), 0, 0, -1)))
        except Exception as e:
            self.logger.error(e)
            self.logger.error("Impossible d'obtenir la date et heure depuis le module GSM")
            return 0
        
    ## Lit un SMS à partir de l'indice donné et renvoie le texte du message et le numéro de l'expéditeur.
    # @param index L'indice du SMS à lire.
    # @return Retourne le message et le numéro de téléphone de l'expéditeur ou un tableau vide en cas d'erreur lors de la lecture.
    def readAllSMS(self):
        buffer = self.sendAT("+CMGL=\"ALL\"",2) # On demande la lecture de tous les SMS
        try:
            buffer = buffer.split("\r\n\r\n")[:-1]
            list_sms = []
            for sms in buffer:
                number = sms.split(",")[2].strip("\"") # On parse la réponse
                text = list(filter(None,sms.split("\r\n")))[1]
                list_sms.append((number,text))
            return list_sms
        except Exception as E:
            self.logger.error(E)
            self.logger.error("Erreur lors de la lecture des SMS")
            return []

    ## Supprime un SMS à partir de son indice.
    # @param index L'indice du SMS à supprimer.
    # @return Retourne la réponse à la commande.
    def deleteSMS(self, index):
        return self.sendAT("+CMGD=" + str(index) + ",0")

    ## Supprime tous les SMS.
    # @return Retourne la réponse à la commande.
    def deleteAllSMS(self):
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
        if word == "seuil":
            self.logger.info("Envoi du seuil limite de la batterie")
            return "Seuil de la batterie : " + str(self.config.getBatteryLimit()) + " mV"
        elif word == "site" or word == "nom":
            self.logger.info("Envoi du nom de la station")
            return "Nom de la station : " + str(self.config.getSiteName())
        elif word == "debut" or word == "début" or word == "eveil" or word == "éveil" or word == "reveil" or word == "réveil":
            self.logger.info("Envoi de l'heure de réveil de la station")
            return "Heure de révéil de la station : " + str(self.config.getWakeupHour()) + " h"
        elif word == "fin" or word == "extinction":
            self.logger.info("Envoi de l'heure d'extinction de la station")
            return "Heure d'extinction de la station : " + str(self.config.getSleepHour()) + " h"
        elif word == "altitude":
            self.logger.info("Envoi de l'altitude de la station")
            return "Altitude de la station : " + str(self.config.getSiteAltitude()) + " m"
        elif word == "logs":
            self.logger.info("Envoi des logs")
            return self.getLogs()
        elif word == "data":
            self.logger.info("Envoi des dernières données")
            return self.getData() #TODO
        elif word == "aide":
            self.logger.info("Envoi de la liste des commandes")
            return "Envoyez n'importe quel message pour obtenir le dernier bulletin météo. \nVotre sms peut aussi contenir l'une des commandes suivantes : batterie?, seuil?, nom?, altitude?, eveil?, extinction?, maitre?"
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
                if(int(arg) >= int(self.config.getSleepHour())):
                    raise Exception("Heure de réveil supérieur à l'heure d'extinction")
                elif(int(arg)<0):
                    raise Exception("Heure de réveil inferieur à 0")
                else:
                     self.config.setWakeupHour(int(arg))
                    
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'heure de réveil")
                return "Heure de réveil incorrecte, merci de n'envoyer qu'un nombre entre 0 et l'heure d'extinction."
            else:
                self.logger.success("L'heure de réveil a été correctement mise à jour : " + str(arg) + "h")
                return "Heure de réveil correctement mise a jour : " + str(arg) + " h"

        elif word == "fin" or word == "extinction":
            try:
                if(int(arg) <= int(self.config.getWakeupHour())):
                    raise Exception("Heure d'extinction inférieur à l'heure d'extinction")
                elif(int(arg)>23):
                    raise Exception("Heure de réveil inferieur à 0")
                else:
                    self.config.setSleepHour(int(arg))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'heure d'extinction")
                return "Heure d'extinction incorrecte, merci de n'envoyer qu'un nombre entre l'heure de réveil et 23."
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
                self.config.setSiteAltitude(int(arg))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour l'altitude")
                return "Altitude incorrecte, merci de n'envoyer qu'un nombre."
            else:
                self.logger.success("L'altitude a été correctement mis à jour : " + str(arg))
                return "Altitude correctement mise a jour : " + str(arg) + " m"
        
        elif word == "seuil":
            try:
                if(int(arg) >= 12000):
                    raise Exception("Seuil trop élevé")
                elif(int(arg)<= 10000):
                    raise Exception("Seuil trop faible")
                else:
                    self.config.setBatteryLimit(str(int(arg)))
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de mettre à jour le seuil de la batterie")
                return "Seuil incorrect, merci de n'envoyer qu'un nombre."
            else:
                self.logger.success("Le seuil de la batterie a été correctement mis à jour : " + str(arg))
                return "Le seuil de la batterie a été correctement mis a jour : " + str(arg) + " mV"
        
        self.logger.info("Commande inconnue")
        return "Commande inconnue."

    ## Répond à tous les SMS reçus.
    # @param sensorsData Le rapport météo sous la forme d'un dictionnaire.
    def respondToSMS(self, sensorsData):
        config_set = False
        self.logger.info("Analyse des SMS reçus...")
        list_sms = self.readAllSMS() #On récupère la liste des indices des SMS
        self.logger.success(str(len(list_sms)) + " SMS reçus")
        i = 0
        for sms in list_sms: #On les parcourt
            i = i + 1
            self.logger.info("Traitement du SMS numéro " + str(i) + "...")
            try:
                self.logger.info("Lecture du SMS : " + str(sms[0]) + " / Message : " + str(sms[1]))
                status = self.getStatus(sms[1]) #On récupère le status (commande, mot de passe, infos)
                if status == 1: #S'il s'agit d'une commande d'écriture
                    if (sms[0] == self.config.getGsmMaster()): #Si le numéro est le bon, on l'autorise
                        self.sendSMS(sms[0], self.executeSetCommand(sms[1])) #On exécute la commande et on réponds le message de confirmation ou d'erreur
                        config_set = True
                    else: #Sinon, on répond que ce n'est pas possible
                        self.logger.info("Permission refusée : ce numéro n'est pas le maître de la station")
                        self.sendSMS(sms[0], "Vous n'avez pas la permission d'effectuer cette commande.")
                elif status == 2: #S'il s'agit d'une commande de lecture, on renvoie la réponse adaptée
                    self.sendSMS(sms[0], self.executeGetCommand(sms[1], sensorsData))
                elif status == 3: #S'il s'agit du mot de passe
                    self.sendSMS(sms[0], "Vous etes désormais le nouveau responsable de la station.")
                    self.config.setGsmMaster(str(sms[0]))
                    config_set = True
                    self.logger.info("Nouveau maître de la station : " + str(sms[0]))
                elif status == 0: #Si ce n'est pas une des 3 possibilités, on renvoie le sms contenant les infos
                    self.sendSMS(sms[0], self.createSMS(sensorsData))
                    self.logger.info("Envoie du bulletin météo")
            except Exception as e:
                self.logger.error(e)
                self.logger.error("Impossible de traiter le SMS numéro "+ str(i))
            else :
                self.logger.success("Traitement du SMS numéro " + str(i) + " terminé")
        
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
        if battery <= int(self.config.getBatteryLimit())-200 and battery != 0:
            self.sendSMS(self.config.getGsmMaster(), "[" +  sensorsData['Time'] + "]\n/!\\ La tension de la batterie (" + str(battery) + " mV) est proche du seuil (" + str(self.config.getBatteryLimit()) + " mV) , la station risque de ne plus fonctionner correctement. /!\\")

        self.sleep()

    def getLogs(self):
        pattern = r"(?P<time>.*) \| (?P<message>.*)"  
        output = ""
        for groups in logger.parse("logs/logs.log", pattern)[:50]:
            output += groups["time"] + " | " + groups["message"] + "\n"
        return output



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
