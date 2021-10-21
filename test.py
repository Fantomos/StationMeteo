import time


buffer = "\"16/12/20,16:01:27+22\""
datetime = buffer.split("\"")[1]
date = datetime.split(",")[0].split("/")
clock = datetime.split(",")[1].split("+")[0].split(":")
date[2] = "20" + date[2]
epochTime= time.mktime((int(date[2]), int(date[1]), int(date[0]), int(clock[0]), int(clock[1]), int(clock[2]), 0, 0, -1))

a = int(epochTime).to_bytes(4, 'big')

b = int.from_bytes(a, byteorder='big', signed=False)


print(b)