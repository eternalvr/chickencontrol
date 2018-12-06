#!/usr/bin/python
import time
import RPi.GPIO as GPIO
from datetime import date
import datetime
import astral
import pytz
import config
import logging
import mqtt
logger = logging.getLogger("LED")
logging.basicConfig(level=config.CONFIG['loglevel'], format='%(asctime)s - %(levelname)s - %(message)s')

def start_led(lastState, p):
  global logger
  loc = astral.Location(('Bochum', 'Germany', 51.4415817, 7.1420979, 'Europe/Berlin', 140))
  led_pin=config.CONFIG['led_pin']

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(led_pin, GPIO.OUT)
  GPIO.setwarnings(False)

  dutyCycle=0
  pwm = GPIO.PWM(led_pin, config.CONFIG['pwm_freq'])
  pwm.start(dutyCycle)
  state='unknown'
  while 1:
      try:
        now=pytz.timezone(config.CONFIG['timezone']).localize(datetime.datetime.now())
        logger.debug( "TIME: " + str(now))
        t30m=datetime.timedelta(minutes=config.CONFIG['light_on_minutes_before_sunset'])

        sun=loc.sun(date=now, local=True)
        logger.debug( "Sunset: " + str(sun['sunset']))
  
        beforesunset=sun['sunset'] - t30m
        logger.debug (str(config.CONFIG['light_on_minutes_before_sunset']) + " min before sunset: " + str(beforesunset))

        delta_sun = now - beforesunset
        logger.debug ("Delta: " + str(delta_sun.total_seconds()))
 
        dt_sleep = datetime.datetime.now(pytz.timezone(config.CONFIG['timezone'])).replace(hour=config.CONFIG['sleep_at_hour'],minute=config.CONFIG['sleep_at_minute'],second=0)
        logger.debug ("Sleep Time: " + str(dt_sleep))

        delta_sleep = now - dt_sleep
        logger.debug ("Delta Sleep: " + str(delta_sleep.total_seconds()))


    # summer mode - sunset is after sleep time - no light necessary
        if delta_sun.total_seconds() < 0 and delta_sleep.total_seconds() > 0:
            dutyCycle=0
            logger.debug("Before sunset but after sleep time, disable light")
            state='disabled'

    # we are before sunset-30 an before sleep_time: lights out
        if delta_sun.total_seconds() < 0 and delta_sleep.total_seconds() < 0:
            dutyCycle=0
            logger.debug("Before Sunset and before sleep time: Lights out")
            state='off'

    # if we are between sunset-30 and sleep_time: full on
        if delta_sun.total_seconds() > 0 and delta_sleep.total_seconds() < 0:
            dutyCycle=100
            logger.debug ("After Sunset and before sleep time: Lights on")
            state = 'on'
  
        # it's after sunset and after sleep time
        if delta_sun.total_seconds() > 0 and delta_sleep.total_seconds() > 0:
            # it's after sleep_time + transition time
            if delta_sleep.total_seconds() > config.CONFIG['sleep_transition_seconds']:
                dutyCycle=0
                logger.debug ("After Sunset and after Sleep and Transition time: Lights off")
                state = 'off'
            else:
                percentage = ( (delta_sleep.total_seconds() / config.CONFIG['sleep_transition_seconds'])) * 100
                dutyCycle=(100-percentage)
                logger.debug ("In Sleep Transition: " + str(dutyCycle) + "%")
                state = 'tr'

        pwm.ChangeDutyCycle(dutyCycle)
        lastState.value = state

        time.sleep(config.CONFIG['time_check_interval'])
      except KeyboardInterrupt:
        logger.info("Keyboard Intterupt. Exit.")
        exit()





