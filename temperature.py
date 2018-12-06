import os
import sys
import time
import config
import logging
logger = logging.getLogger("TEMP")
logging.basicConfig(level=config.CONFIG['loglevel'] )

def aktuelleTemperatur():
      
    # 1-wire Slave Datei 
    file = open(config.CONFIG['temperature_device'])
    filecontent = file.read()
    file.close()
 
    # Temperaturwerte auslesen und konvertieren
    stringvalue = filecontent.split("\n")[1].split(" ")[9]
    temperature = float(stringvalue[2:]) / 1000
 
    # Temperatur ausgeben
    rueckgabewert = '%6.2f' % temperature 
    return(rueckgabewert)

def start_temperature( lastTemperature, p ):
    try:
      logger.info("Starting Temperature reading")
      while 1:
        lastTemperature.value = float(aktuelleTemperatur())
        time.sleep(config.CONFIG['temperature_interval'])
    except KeyboardInterrupt:
        exit()
