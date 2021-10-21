

class Sigfox:
    def __init__(self, i2c_bus, logger, message_length, i2c_address):
        self.i2c_bus = i2c_bus
        self.message_length = message_length
        self.i2c_address = i2c_address
        self.logger = logger

   