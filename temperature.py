import os
import sys
import time
import config
import logging
logger = logging.getLogger("TEMP")
logging.basicConfig(level=config.CONFIG['loglevel'] )

def aktuelleTemperatur(filename):
    try:  
      # 1-wire Slave Datei 
      file = open(filename)
      lines = file.readlines()
      file.close()
 
      if lines[0].strip() [-3:] != 'YES':
	logger.debug("Error with sensor: " + filename)  
        return 0
      temp_line = lines[1].find('t=')
      if temp_line != -1:
        temp_output = lines[1].strip() [temp_line+2:]
        temp_celsius = float(temp_output) / 1000
      return temp_celsius 
    except e:
      logger.debug("Error: " + str(e))
      return 0

def start_temperature( results, p ):
    try:
      logger.info("Starting Temperature Process")
      while 1:

        for name in config.CONFIG['temperature_devices']:
           filename = config.CONFIG['temperature_devices'][name]
           res = aktuelleTemperatur(filename)
           results[name] = str(res)#float(aktuelleTemperatur(filename))

        time.sleep(config.CONFIG['temperature_interval'])
    except KeyboardInterrupt:
        exit()
