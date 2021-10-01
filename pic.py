from imports import *
import gsm

#Fonction permettant de lire la valeur d'un registre du PIC. Renvoie 100000 en cas d'erreur.
def lecture(reg):
    sleep(0.05) #Délai sinon ça marche pas
    try:
        bus.write_byte(pic_addr, reg)  #On envoie d'abord l'adresse du registre
        return bus.read_byte(pic_addr) #On lit ensuite la valeur qui arrive
    except:
        logger.error("Impossible de lire le registre " + str(reg) + " sur le PIC.")
        return 100000

#Ecrit une valeur donnée (data) dans un registre donné (reg)
def ecriture(reg, data):
    try:
        bus.write_byte_data(pic_addr, reg, data)
    except:
        logger.error("Impossible d'envoyer les données au PIC (registre=" + str(reg) + ", données=" + str(data) + ").")

#Envoie la date et l'heure reçus depuis le GSM au PIC au format [année, mois, jour, heure, minute, seconde]
def setDateTime(dt):
    if len(dt) == 6: #Si on les a récupérés correctement
        datetime = [dec2bcd(int(i)) for i in dt] #On les convertit en BCD et on les envoie
        ecriture(pic_year, datetime[0])
        ecriture(pic_month, datetime[1])
        ecriture(pic_wd, 0)
        ecriture(pic_day, datetime[2])
        ecriture(pic_hour, datetime[3])
        ecriture(pic_min, datetime[4])
        ecriture(pic_sec, datetime[5])
    return dt

def resetWatchdogTimer():
    lecture(0)

#Permet de lire toutes les données du PIC concernant le vent. Renvoie 100000 en cas d'erreur.
def readData():
    try:
        while lecture(pic_state) != 1: #Tant que le PIC n'a pas fini ses mesures on attend
            sleep(0.5)
        
        direction_vent = lecture(pic_dir_vent) #On lit la direction du vent (entre 0 et 15)
        vitesse_fort = lecture(pic_vent_h)     #On lit l'octet de poids fort de la vitesse du vent
        vitesse_faible = lecture(pic_vent_l)   #On lit l'octet de poids faible de la vitesse du vent
        if vitesse_fort == 100000 or vitesse_faible == 100000: #Si la lecture de la vitesse a eu un problème, on renvoie 100000
            return direction_vent, 100000
        else:
            return direction_vent, (vitesse_fort * 256 + vitesse_faible) / 10
    except:
        logger.error("Impossible de lire les données du PIC.")
        return 100000, 100000