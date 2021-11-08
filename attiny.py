class Attiny:
    def __init__(self, i2c_bus, logger, i2c_address):
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.logger = logger

    register =	{
            "sleep" : 0xD8,
            "eveil" : 0xD0,
            "alarm_min_val" : 0x00,
            "alarm_sec_val" : 0x45
    }

    
    def getWindData(self):
        return {"Direction":0, "Speed":0, "DirectionMax":0, "SpeedMax":0}
