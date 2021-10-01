
#Port série pour le GSM
def initGSM(): 
    try:
        gsm_port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=1)
    except:
        logger.error("Impossible d'ouvrir le port série pour le module GSM.")
        gsm_port = None
    return gsm_port
    
#Vide le buffer
def readBuffer():
    try:
        buffer = gsm_port.read(1000).decode("8859")
        output = buffer
        while (len(buffer) > 0):
            sleep(0.2)
            buffer = gsm_port.read(1000).decode("8859")
            output += buffer
        return output.strip()
    except:
        logger.error("Erreur lors de la lecture du buffer.")
        return ""

#Envoie une commande AT sans avoir besoin d'écrire "AT" ou \r\n
def sendAT(command, start = "AT"):
    try:
        readBuffer()  #On vide le buffer avant
        sleep(0.2)
        gsm_port.write((start + command + "\r\n").encode("8859")) #On écrit la commande
        return readBuffer() #On renvoie la réponse
    except:
        logger.error("Erreur lors de l'envoi de la commande " + str(command) + ".")
        return "error"
        
#On envoie une impulsion de 2 sec sur la pin POWER du module GSM
def power():
    io.setmode(io.BOARD)
    io.setup(gsm_power, io.OUT)
    io.output(gsm_power, io.HIGH)
    sleep(1)
    io.output(gsm_power, io.LOW)
    sleep(1)
    io.setup(gsm_power, io.IN)

#Allume le module GSM (power + commande vide) et renvoie le résultat d'une commande simple
def turnOn():
    if sendAT("") != "OK":
        power()
        return "OK"
    else:
        return "not OK"

#Eteint la station
def turnOff():
    if sendAT("") == "OK":
        power()
    return "OK"

#Entre le code PIN de la carte SIM
def enterPIN():
    return sendAT("+CPIN=\"0000\"")

#Envoie les commandes nécessaires pour envoyer des SMS
def setupSMS():
    output = sendAT("+CMGF=1") #Met en mode texte
    output += sendAT("+CSCS=\"GSM\"") #Indique un encodage GSM
    sendAT("+CPMS=\"SM\"") #Indique que le stockage se fait dans la carte SIM
    return output

#Envoie un seul SMS au numéro indiqué
def sendSingleSMS(numero, txt):
    output = sendAT("+CMGS=\"" + numero + "\"") #On envoie le numéro
    output += sendAT(txt[:159], "") #On envoie le texte du SMS
    output += sendAT("\x1A", "") #On envoie le caractère de fin
    sleep(0.1)
    readBuffer() #On vide le buffer
    return output

#Envoie autant de SMS que nécessaire au numéro indiqué pour envoyer le texte indiqué
def sendSMS(numero, txt):
    output = []
    sms_list = [txt[150*i:150*(i+1)] for i in range(1+len(txt) // 150)] #On découpe le texte en morceau d'au plus 150 caractères de long
    for i in range(len(sms_list)): #On envoie chaque morceau
        output.append(sendSingleSMS(numero, sms_list[i]))
        if i < len(sms_list) - 1: #Si ce n'est pas le dernier morceau, on attend avant le prochain
            sleep(1.5)
    readBuffer()
    return ",".join(output)

#Renvoie la date sous la forme d'un tableau [année, mois, jour, heure, minute, seconde]
def getDateTime():
    buffer = sendAT("+CCLK?") #On récupère la date et heure du module GSM
    if len(buffer) > 17: #Si on a bien tout reçu, on le renvoie, sinon on renvoie un tableau vide
        datetime = buffer.split("\"")[1]
        date = datetime.split(",")[0]
        time = datetime.split(",")[1].split("+")[0]
        return date.split("/") + time.split(":")
    else:
        return []
    
#Renvoie le nombre de SMS dans la mémoire de la carte
#on reçoit une réponse sous la forme "+CPMS: x,y,x,y,x,y", où x est le nombre de message stocké et y la capacité
def getSMSCount():
    buffer = sendAT("+CPMS=\"SM\"")
    try:
        return int(buffer[7:].split(",")[0])
    except:
        return -1
    
#Renvoie les index des SMS enregistrés (nombre entre 1 et 50]
def getSMSIndexes():
    buffer = sendAT("+CMGL=\"ALL\"").split("\r\n")
    indexes = []
    for data in buffer:
        if data.startswith("+CMGL"):
            try:
                index = data[7:].split(",")[0]
                if not index in indexes:
                    indexes.append(index)
            except:
                logger.error("Erreur dans la récupération des index")
    return indexes

#Lit un SMS à partir de l'indice donné et renvoie le texte du message et le numéro de l'expéditeur
def readSMS(index):
    readBuffer()
    buffer = sendAT("+CMGR=" + str(index)) #On demande le SMS
    data = buffer.split("\r\n")
    sleep(0.1)
    try:
        number = data[0].split(",")[1].strip("\"")
        body = data[1]
        return [convertToAscii(body), number]
    except:
        logger.error("Erreur lors de la lecture du SMS d'indice " + str(index))
        return []

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

#Supprime un SMS à partir de son indice
def deleteSMS(index):
    sleep(0.1)
    return sendAT("+CMGD=" + str(index) + ",0")

def deleteAllSMS():
    sleep(0.1)
    readBuffer()
    return sendAT("+CMGD=0,4")

#Renvoie le status d'un sms.
#0 = SMS normal (dans tous les cas sauf ceux ci-dessous)
#1 = commande pour modifier un paramètre (si le texte contient "=" et une commande valide)
#2 = commande pour lire un paramètre (si le texte contient "?" et une commande valide)
#3 = mot de passe reçu (si le texte contient le mot de passe)
def getStatus(sms):
    if len(sms) > 1:
        sms = sms[0]
        if ("=" in sms and sms.split("=")[0].lower().strip() in gsm_commands):
            return 1
        elif ("?" in sms and sms.split("?")[0].lower().strip() in gsm_commands):
            return 2
        elif (conf_password in sms):
            return 3
        else:
            return 0
    else:
        return -1

#Exécute une commande de lecture de paramètre à partir du texte du sms et renvoie la réponse
def executeGetCommand(command):
    #On récupère ce qui est avant le ?, on le met en minuscule et on enlève les espaces avant et après
    word = command.split("?")[0].lower().strip()
    print("command : " + word)
    #Selon la commande, on effectue différentes actions
    if word == "batterie":
        return str(pic.lecture(pic_batterie) / 10) + " V"
    elif word == "site" or word == "nom":
        return "Site : \n" + config.getSite()
    elif word == "debut" or word == "début":
        return "Heure d'éveil de la station : " + config.getHeureEveil() + " h"
    elif word == "fin":
        return "Heure d'extinction de la station : " + config.getHeureSleep() + " h"
    elif word == "altitude":
        return "Altitude de la station : " + config.getAltitude() + " m"
    elif word == "logs":
        return config.getNLogs(command.split("?")[1].strip() if command.split("?")[1].strip().isnumeric() else 1)
    elif word == "data":
        return config.getData()
    elif word == "maitre" or word == "maître":
        return "Numéro maître de la station :\n" + config.getMasterNumber()
    
    return "Commande inconnue."

#Exécute une commande de modification de paramètres à partir d'un sms, et renvoie la réponse
def executeSetCommand(command):
    #On récupère ce qui est de part et d'autres du =, on met le premier en minuscule et on enlève les espaces avant et après
    word = command.split("=")[0].lower().strip()
    arg = command.split("=")[1].strip()
    #Selon la commande, on effectue différentes actions
    if word == "debut" or word == "début":
        result = config.setHeureEveil(arg)
        if result:
            return "Heure d'éveil correctement mise à jour : \n" + str(arg) + " h"
        else:
            return "Heure d'éveil incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
    elif word == "fin":
        result = config.setHeureSleep(arg)
        if result:
            return "Heure d'extinction correctement mise à jour : \n" + str(arg) + " h"
        else:
            return "Heure d'extinction incorrecte, merci de n'envoyer qu'un nombre entre 0 et 23."
    elif word == "site" or word == "nom":
        result = config.setSite(arg)
        if result:
            return "Site correctement mis à jour : \n\"" + str(arg[:125]) + "\""
        else:
            return "Une erreur est survenue, merci de réessayer."
    elif word == "altitude":
        result = config.setAltitude(arg)
        if result:
            return "Altitude correctement mise à jour : \n" + str(arg) + " m"
        else:
            return "Altitude incorrecte, merci de n'envoyer qu'un nombre."
    
    return "Commande inconnue."

#Crée le String à envoyer par SMS pour transmettre les informations
#Pour chaque valeur, on écrit "n/a" si la valeur n'a pas été trouvée
def createSMS(temperature, vitesse_moy, vitesse_max, direction_moy, direction_max, pression, humidite, hauteur_nuages, heure_mesures):
    temperature = str(round(temperature, 1)) if float(temperature) < 1000 else "n/a"
    vitesse_moy = str(int(vitesse_moy)) if int(vitesse_moy) < 1000 else "?"
    vitesse_max = str(int(vitesse_max)) if int(vitesse_max) < 1000 else "?"
    direction_moy = direction_moy if int(direction_moy) < 1000 else 16
    direction_max = direction_max if int(direction_max) < 1000 else 16
    pression = str(int(pression)) if int(pression) < 10000 else "n/a"
    humidite = str(int(humidite)) if int(humidite) < 1000 else "n/a"
    hauteur_nuages = str(int(hauteur_nuages)) if int(hauteur_nuages) < 10000 else "n/a"
    
    output = "[" + str(heure_mesures) + "]\n"
    output += "Temp: " + temperature + " C\n"
    output += "Vent moy: " + vitesse_moy + "km/h " + directions_vent_string_sms[direction_moy] + "\n"
    output += "Vent max: " + vitesse_max + "km/h " + directions_vent_string_sms[direction_max] + "\n"
    output += "Humi: " + humidite + "%\n"
    output += "Press: " + pression + "hPa\n"
    output += "Haut nuages: " + hauteur_nuages + "m"
    #On ajoute le nom du site et on coupe à 158 caractères pour éviter d'envoyer 2 SMS
    if len(output) < 158:
        output = (config.getSite() + " (" + config.getAltitude() + " m)")[:157-len(output)] + "\n" + output
    else:
        output = output[:158]
    return output

#Répond à tous les SMS reçus
def respondToSMS(temperature, humidite, pression, altitude, hauteur_nuages, direction_vent, vitesse_vent, direction_vent_moy, direction_vent_max, vitesse_vent_moy, vitesse_vent_max, heure_mesures):
    master_number = config.getMasterNumber() #On récupère le numéro maître de la station
    if gsm.getSMSCount() > 0: #Si on a reçu des SMS
        indexes = gsm.getSMSIndexes() #On récupère la liste des indices des SMS
        for index in indexes[:20]: #On les parcourt
            sms = gsm.readSMS(index) #On lit le sms (format [message, numéro])
            print(index, sms)
            status = gsm.getStatus(sms) #On récupère le status (commande, mot de passe, infos)
            if status == 1: #S'il s'agit d'une commande d'écriture
                if (sms[1] == master_number): #Si le numéro est le bon, on l'autorise
                    gsm.sendSMS(sms[1], gsm.executeSetCommand(sms[0])) #On exécute la commande et on réponds le message de confirmation ou d'erreur
                else: #Sinon, on répond que ce n'est pas possible
                    gsm.sendSMS(sms[1], "Vous n'avez pas la permission d'effectuer cette commande.")
            elif status == 2: #S'il s'agit d'une commande d'écriture, on renvoie la réponse adaptée
                gsm.sendSMS(sms[1], gsm.executeGetCommand(sms[0]))
            elif status == 3: #S'il s'agit du mot de passe
                if config.setMasterNumber(sms[1]): #On modifie le numéro maître, et on prévient
                    gsm.sendSMS(sms[1], "Vous etes désormais le nouveau responsable de la station.")
                    master_number = sms[1]
                else: #Si une erreur est survenue, on prévient
                    gsm.sendSMS(sms[1], "Une erreur est survenue, veuillez réessayer.")
            elif status == 0: #Si ce n'est pas une des 3 possibilités, on renvoie le sms contenant les infos
                gsm.sendSMS(sms[1], sensors.createSMS(temperature, vitesse_vent_moy, vitesse_vent_max, direction_vent_moy, direction_vent_max, pression, humidite, hauteur_nuages, heure_mesures))
            #gsm.deleteSMS(index) #On supprime le SMS après la réponse
            sleep(0.1)
            pic.resetWatchdogTimer()
        #On supprime tous les SMS
        gsm.deleteAllSMS()
        sleep(3)
    
    #On mesure la tension de la batterie, et s'il elle sous le seuil d'alerte, on envoie un message
    tension_batterie = pic.lecture(pic_batterie) / 10
    if tension_batterie <= seuil_batterie:
        gsm.sendSMS(master_number, "[" + heure_mesures + "]\n/!\\ La tension de la batterie est faible (" + str(tension_batterie) + " V), la station risque de ne plus fonctionner correctement. /!\\")

