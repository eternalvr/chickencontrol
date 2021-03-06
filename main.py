#!/usr/bin/python
import json
import pytz
import logging
import led
import mqtt
import config
import temperature
import motor
from multiprocessing import Process
import multiprocessing
import time
import ctypes
import datetime
active = {}
logger = 0
lastState = lastTemperature = lastMotorState = 0
client = 0

active_modules = {}

def start():
    global logger, client, lastState, lastTemperature, lastMotorState, active_modules
    try:
        logger = logging.getLogger()
        logging.basicConfig(level=config.CONFIG['loglevel'])
        client = mqtt.initialize_mqtt()

        results = multiprocessing.Manager().dict()


        lastState = multiprocessing.Value(ctypes.c_char_p, b"undefined")
        lastTemperature = multiprocessing.Value(ctypes.c_float, 0)
        lastMotorState = multiprocessing.Value(ctypes.c_char_p, b"unknown")

        # start led process

        active_modules = { 'led' : { 'target' : led.start_led, 'args' : results },
                            'temp' : { 'target' : temperature.start_temperature, 'args' : results },
                            'motor' : { 'target' : motor.start_motor, 'args' : results }
                            }

        check_processes_alive()

        while 1:
            check_processes_alive()
            publish(logger, client, results)
            time.sleep(10)

    except KeyboardInterrupt:
       logger.info("Exiting.")
       exit()

def check_processes_alive():
    global active

    for m in active_modules:
        if not m in active or active[m].is_alive() == False:
          logger.info("Starting Process: " + m)
          active[m] = create_new_process(m, active_modules[m]['target'], (active_modules[m]['args'],1))


def create_new_process(ptype, target, args):
    t = Process(name=ptype, target=target, args=args)
    t.daemon = True
    t.start()
    return t

def publish(logger, client, results):
    #values = { 'lightState' : lastState.value, 'temperature' : lastTemperature.value, 'motorState' : lastMotorState.value, 'lastMessage' : str(pytz.timezone(config.CONFIG['timezone']).localize(datetime.datetime.now()))}
    results['lastMessage'] = str(pytz.timezone(config.CONFIG['timezone']).localize(datetime.datetime.now()))
    
    logger.debug(str(results))

    client.publish(config.CONFIG['mqtt_topic'] + "/SENSOR", json.dumps(results._getvalue()))
    
if __name__ == '__main__':
    start()
