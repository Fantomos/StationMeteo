
from voxpopuli import Voice
from time import sleep
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from pygame import mixer
import RPi.GPIO as GPIO

class Radio:
    def __init__(self, config, logger, speed = 100, pitch = 40, tw_gpio = 29, ptt_gpio = 31):
        self.config = config
        self.logger = logger
        self.tw_gpio = tw_gpio
        self.ptt_gpio = ptt_gpio

        # Configure les pins en sortie
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.tw_gpio, GPIO.OUT)
        GPIO.setup(self.ptt_gpio, GPIO.OUT)
        try:
            self.voice = Voice(lang="fr", voice_id=1, speed=speed, pitch=pitch)
            mixer.init(frequency=16000) #Initialisation du lecteur audio à 16kHz d'échantillonnage pour correspondre aux fichiers audio
        except:
            self.logger.error("Impossible de charger la synthèse vocale ou le codec audio")
            self.voice = None

    #Crée le message qui sera lu par la radio
    #Pour chaque valeur, on écrit "erreur" si la valeur n'a pas été trouvée
    def createRadioMessage(self,sensorsData):
        temperature = str(round(sensorsData['Temperature'], 1)).replace(".", ",").replace(",0", "") if float(sensorsData['Temperature']) < 100 else "erreur"
        direction = str(round(sensorsData['Direction'],0)) if float(sensorsData['Direction']) < 1000 else "erreur"
        direction_max = str(round(sensorsData['Direction_max'],0)) if float(sensorsData['Direction_max']) < 1000 else "erreur"
        speed = str(round(sensorsData['Speed'], 0)).replace(".", ",").replace(",0", "") if float(sensorsData['Speed']) < 1000 else "erreur"
        speed_max = str(round(sensorsData['Speed_max'], 0)).replace(".", ",").replace(",0", "") if float(sensorsData['Speed_max']) < 1000 else "erreur"
        output = "Site de. " + self.config.getSiteName() + ". "
        output += "Vent moyen : " + speed + " " + " kilomètres par heure . . " + direction + " degrés . "
        output += "Vent maximal : " + speed_max + " " + " kilomètres par heure . . " + direction_max + " degrés . "
        output += "Température : " + temperature + " degrés"
        return output


    #Joue le message sonore par la radio, et gère la partie I/O associée
    def playVoiceMessage(self, sensorsData):
        self.logger.info("Lecture du message audio...")
        if self.voice != None:
            #On génère et on enregistre le message
            wav = self.voice.to_audio(self.createRadioMessage(sensorsData))
            with open("radio.wav", "wb") as wavfile:
                wavfile.write(wav)
            #On allume la radio, puis le PTT
            GPIO.output(self.tw_gpio, GPIO.HIGH)
            sleep(0.5)
            GPIO.output(self.ptt_gpio, GPIO.HIGH)
            sleep(0.2)
            #On joue un bip d'introduction
            self.playSound("bip.wav")
            sleep(0.7)
            #On joue le message
            self.playSound("radio.wav")
            #On éteint le PTT et la radio
            sleep(0.5)
            GPIO.output(self.ptt_gpio, GPIO.LOW)
            sleep(0.1)
            GPIO.output(self.tw_gpio, GPIO.LOW)
            mixer.quit()
            self.logger.success("Lecture terminée")
        else:
            self.logger.error("Impossible de jouer le message audio car les modules ne sont pas initialisés.")
            

    #Joue un son à partir de son chemin d'accès. On peut également préciser si on doit attendre avant de continuer l'exécution
    def playSound(self, path):
        #On charge le son, on le joue, puis on attend qu'il soit fini
        sound = mixer.Sound(path)
        sound.play()
        while mixer.get_busy():
            continue
        