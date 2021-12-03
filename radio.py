
## @file radio.py
# Définition de la classe Radio. Elle permet la manipulation de la radio et l'utilisation de la synthèse vocale pour générer un message.
##
from voxpopuli import Voice
from time import sleep
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pygame import mixer
import pigpio
import threading

## Classe Radio. 
#  Cette classe permet la communication du rapport météo par la radio. Elle utilise une synthèse vocale sous le nom de Voxpopuli. La fonction mixer de PyGame est utilisé pour lire les fichiers audios générés.
class Radio:
    
    ## Constructeur.
    # @param config Objet ConfigFile.
    # @param logger Logger principal.
    # @param pi Instance de pigpio.
    # @param speed Vitesse de la lecture du message par la synthèse vocale. La valeur par défaut est 100.
    # @param pitch Pitch de la lecture du message par la synthèse vocale. La valeur par défaut est 40.
    # @param tw_gpio Numéro de pin pour alimenter le talkie-walkie. La valeur par défaut est 29.
    # @param ptt_gpio Numéro de pin pour le push-to-talk du talkie-walkie. La valeur par défaut est 31.
    def __init__(self, config, logger, pi,speed = 100, pitch = 40, tw_gpio = 29, ptt_gpio = 31):
        ##  Objet ConfigFile.
        self.config = config
        ##  Logger principal.
        self.logger = logger
        ## Instance pigpio
        self.pi = pi
        ## Numéro de pin pour alimenter le talkie-walkie.
        self.tw_gpio = tw_gpio
        ## Numéro de pin pour le push-to-talk du talkie-walkie.
        self.ptt_gpio = ptt_gpio

        # Configure les pins en sortie
        self.pi.set_mode(self.tw_gpio, pigpio.OUTPUT)
        self.pi.set_mode(self.ptt_gpio, pigpio.OUTPUT)
        self.pi.write(self.tw_gpio,0)
        self.pi.write(self.ptt_gpio,0)

        try:
            ## Référence de l'objet Voice de la synthèse vocale
            self.voice = Voice(lang="fr", voice_id=1, speed=speed, pitch=pitch)
            mixer.init(frequency=16000) #Initialisation du lecteur audio à 16kHz d'échantillonnage pour correspondre aux fichiers audio
        except:
            self.logger.error("Impossible de charger la synthèse vocale ou le codec audio")
            self.voice = None

    ## Crée le message qui sera lu par la radio. Pour chaque valeur, on écrit "erreur" si elle n'est pas acccessible.
    # @param sensorsData Les données des capteurs.
    # @return Retourne le message sous la forme d'une chaîne de caractère.
    def createRadioMessage(self,sensorsData):
        temperature = str(round(sensorsData['Temperature'], 1)).replace(".", ",").replace(",0", "") if float(sensorsData['Temperature']) < 100 and float(sensorsData['Temperature']) > -50 else "erreur"
        direction = str(round(sensorsData['Direction'],0)) if float(sensorsData['Direction']) < 360 and float(sensorsData['Direction']) >= 0 else "erreur"
        direction_max = str(round(sensorsData['Direction_max'],0)) if float(sensorsData['Direction_max']) < 360 and float(sensorsData['Direction_max']) >= 0 else "erreur"
        speed = str(round(sensorsData['Speed'], 0)).replace(".", ",").replace(",0", "") if float(sensorsData['Speed']) < 300 and float(sensorsData['Speed']) >= 0 else "erreur"
        speed_max = str(round(sensorsData['Speed_max'], 0)).replace(".", ",").replace(",0", "") if float(sensorsData['Speed_max']) < 300 and float(sensorsData['Speed']) >= 0 else "erreur"
        output = "Site de. " + self.config.getSiteName() + ". "
        output += "Vent moyen : " + speed + " " + " kilomètres par heure . . " + direction + " degrés . "
        output += "Vent maximal : " + speed_max + " " + " kilomètres par heure . . " + direction_max + " degrés . "
        output += "Température : " + temperature + " degrés"
        return output


    ## Joue le message sonore par la radio, et gère la partie I/O associée.
    # @param sensorsData Les données des capteurs.
    def playVoiceMessage(self, sensorsData):
        self.logger.info("Lecture du message audio...")
        if self.voice != None:
            #On génère et on enregistre le message
            wav = self.voice.to_audio(self.createRadioMessage(sensorsData))
            with open("radio.wav", "wb") as wavfile:
                wavfile.write(wav)
            #On allume la radio, puis le PTT
            self.pi.write(self.tw_gpio,1)
            sleep(1)
            self.pi.write(self.ptt_gpio,1)
            sleep(1)
            #On joue un bip d'introduction
            self.playSound("bip.wav")
            sleep(1)
            #On joue le message
            self.playSound("radio.wav")
            #On éteint le PTT et la radio
            sleep(1)
            self.pi.write(self.ptt_gpio,0)
            sleep(1)
            self.pi.write(self.tw_gpio,0)
            mixer.quit()
            self.logger.success("Lecture terminée")
        else:
            self.logger.error("Impossible de jouer le message audio car les modules ne sont pas initialisés.")
            

    ## Joue un son à partir de son chemin d'accès.
    # @param path Le chemin d'accés du fichier audio.
    def playSound(self, path):
        #On charge le son, on le joue, puis on attend qu'il soit fini
        sound = mixer.Sound(path)
        sound.play()
        while mixer.get_busy():
            continue
        