import configparser


config = configparser.ConfigParser()
config.read('test.ini')

gpio_var = config['GPIO']
dht11_gpio =  gpio_var.getint('dht11_gpio',23)
dht11_gpio = 10
with open('test.ini', 'w') as configfile:
    config.write(configfile)