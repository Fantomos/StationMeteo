import configparser

config = configparser.ConfigParser()
config.read('config.ini')

gpio_var = config['GPIO']
gsm_power_gpio = gpio_var.getint('gsm_power_gpio',12)
dht11_gpio =  gpio_var.getint('dht11_gpio',23)
cmd_tw_gpio = gpio_var.getint('cmd_tw_gpio',29)
ptt_gpio = gpio_var.getint('ptt_gpio',31)
extinction_gpio = gpio_var.getint('extinction_gpio',22)

seuil_alerte = config['BATTERIE'].getfloat('seuil_alerte',11.5)

gsm_var = config['GSM']
gsm_pin = gsm_var.get('gsm_pin','0000')
gsm_password = gsm_var.get('gsm_password','Kews')
gsm_master = gsm_var.get('gsm_master','+33780041476')
gsm_commands = ["batterie", "site", "nom", "debut", "début", "fin", "altitude", "logs", "data", "maitre", "maître"]

mesures_var = config['MESURES']
mesures_nbtry = mesures_var.getint('n_try', 5)
mesures_nbmesures = mesures_var.getint('n_mesures', 1)

nuages_var = config['NUAGES']
nuages_dewb = nuages_var.getfloat('dew_b', 237.7)
nuages_dewa = nuages_var.getfloat('dew_a', 17.27)
nuages_K = nuages_var.getfloat('nuages_K', 122.7)

tts_var = config['TTS']
tts_speed = tts_var.getint('speed_tts', 120)
tts_pitch = tts_var.getint('pitch_tts', 30)

reveil_var = config['REVEIL']
reveil_wakeup = reveil_var.getint('wakeup', 10)
reveil_sleep = reveil_var.getint('sleep', 18)

info_var = config['INFO']
info_nom = info_var.get("nom", 'Position inconnue')
info_altitude = info_var.getint("altitude", 0)



def bcd2dec(bcd):
     return int(str(hex(bcd))[2:])

def dec2bcd(dec):
    return int("0x" + str(dec), 16)

def isInt(i):
    try:
        int(i)
        return True
    except:
        return False

##FICHIERS DE CONFIGURATION






#Paramètres de calcul de la base des nuages


saved_data_count = 3 #Nombre de données à conserver (3 = 10 minutes)



#Paramètres Sigfox
string_keys = {'site':0, 'altitude':1}


#Tableau de conversion pour la direction du vent
#0 : Ouest, 4 : Nord, 8 : Est, 12 : Sud
directions_vent_string = ["ouest",
                      "ouest nord ouest",
                      "nord ouest",
                      "nord nord ouest",
                      "nord",
                      "nord nord èste",
                      "nord èste",
                      "èste nord èste",
                      "èste",
                      "èste sud èste",
                      "sud èste",
                      "sud sud èste",
                      "sud",
                      "sud sud ouest",
                      "sud ouest",
                      "ouest sud ouest",
                      "inconnue"]

directions_vent_string_sms = ["O",
                      "ONO",
                      "NO",
                      "NNO",
                      "N",
                      "NNE",
                      "NE",
                      "ENE",
                      "E",
                      "ESE",
                      "SE",
                      "SSE",
                      "S",
                      "SSO",
                      "SO",
                      "OSO",
                      "?"]


sigfox_addr = 0x55
pic_addr = 0x21


###REGISTRES DU PIC
#Registres liés à la date
pic_year = 0x0
pic_month = 0x1
pic_wd = 0x2
pic_day = 0x3
pic_hour = 0x4
pic_min = 0x5
pic_sec = 0x6

#Registres liés à l'alarme
pic_alm_month = 0x7
pic_alm_wd = 0x8
pic_alm_day = 0x9
pic_alm_hour = 0xA
pic_alm_min = 0xB
pic_alm_sec = 0xC
pic_alrmcon = 0xD
pic_rtccal = 0xE
pic_alrmrpt = 0xF

#Registres de stockage d'information
pic_vb0gpr = 0x10
pic_vb1gpr = 0x11
pic_vb2gpr = 0x12
pic_vb3gpr = 0x13

#Registres liés à la mesure du vent
pic_dir_vent = 0x14
pic_vent_h = 0x15
pic_vent_l = 0x16

#Autres
pic_state = 0x17 #Permet de savoir si le PIC a fini ses mesures
pic_batterie = 0x18 #Permet de récupérer la tension de la batterie

#PIC VALEURS
pic_alrmcon_sleep = 0xD8
pic_alrmcon_eveil = 0xD0
pic_alm_min_val = 0x00
pic_alm_sec_val = 0x45


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

