from imports import *

#Crée le message qui sera lu par la radio
#Pour chaque valeur, on écrit "erreur" si la valeur n'a pas été trouvée
def createRadioMessage(temperature, direction_moy, direction_max, vitesse_moy, vitesse_max):
    temperature = str(round(temperature, 1)).replace(".", ",").replace(",0", "") if float(temperature) < 1000 else "erreur"
    direction_moy = direction_moy if int(direction_moy) < 1000 else 16
    direction_max = direction_max if int(direction_max) < 1000 else 16
    vitesse_moy = str(round(vitesse_moy, 0)).replace(".", ",").replace(",0", "") if int(vitesse_moy) < 1000 else "erreur"
    vitesse_max = str(round(vitesse_max, 0)).replace(".", ",").replace(",0", "") if int(vitesse_max) < 1000 else "erreur"
    output = "Site de. " + config.getSite().replace("INSA", "ine sa") + ". "
    output += "Vent moyen : " + vitesse_moy + " " + " kilomètres par heure . . " + directions_vent_string[direction_moy] + ". "
    output += "Vent maximal : " + vitesse_max + " " + " kilomètres par heure . . " + directions_vent_string[direction_max] + ". "
    output += "Température : " + temperature + " degrés"
    return output


#Création de l'objet de synthèse vocale
def initSpeechSynthesis(mspeed, mpitch):
    try:
        voice = Voice(lang="fr", voice_id=1, speed=mspeed, pitch=mpitch)
        # mixer.init(frequency=16000) #Initialisation du lecteur audio à 16kHz d'échantillonnage pour correspondre aux fichiers audio
    except:
        logger.error("Impossible de charger la synthèse vocale.")
        voice = None
    return voice


#Joue le message sonore par la radio, et gère la partie I/O associée
def playVoiceMessage():
    if voice != None:
        #On génère et on enregistre le message
        wav = voice.to_audio(sensors.createRadioMessage(temperature, direction_vent_moy, direction_vent_max, vitesse_vent_moy, vitesse_vent_max))
        with open("radio.wav", "wb") as wavfile:
            wavfile.write(wav)
        #On allume la radio, puis le PTT
        io.output(io_cmd_tw, io.HIGH)
        sleep(0.5)
        io.output(io_ptt, io.HIGH)
        sleep(0.2)
        #On joue un bip d'introduction
        playSound("bip.wav")
        sleep(0.7)
        #On joue le message
        playSound("radio.wav")
        #On éteint le PTT et la radio
        sleep(0.5)
        io.output(io_ptt, io.LOW)
        sleep(0.1)
        io.output(io_cmd_tw, io.LOW)
    else:
        logger.error("L'objet voice n'a pas été créé, le message ne peut donc pas être généré.")
        

#Joue un son à partir de son chemin d'accès. On peut également préciser si on doit attendre avant de continuer l'exécution
def playSound(path):
    #On charge le son, on le joue, puis on attend qu'il soit fini
    sound = mixer.Sound(path)
    sound.play()
    while mixer.get_busy():
        continue