from loguru import logger
import dateutil

pattern = r"(?P<time>.*) \| (?P<message>.*)"  
output = ""
for groups in logger.parse("logs/logs.txt", pattern):
    output += groups["time"] + " | " + groups["message"] + "\n"

print(output)