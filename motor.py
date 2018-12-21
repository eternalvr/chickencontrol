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

timezone="Europe/Berlin"

sleep_transition_seconds=30

pwm_freq=100

loc = astral.Location((config.CONFIG['led_astral_city'], config.CONFIG['led_astral_country'], config.CONFIG['led_astral_latitude'], config.CONFIG['led_astral_longitude'], config.CONFIG['led_astral_timezone'], config.CONFIG['led_astral_height']))
state = 'unknown'
logger = logging.getLogger("MOTOR")
logging.basicConfig(level=config.CONFIG['loglevel'] )

top_pin = config.CONFIG['motor_stop_top_pin']
bottom_pin = config.CONFIG['motor_stop_bottom_pin']
pin_up = config.CONFIG['motor_pin_up']
pin_down = config.CONFIG['motor_pin_down']
motor_manual_up_pin = config.CONFIG['motor_manual_up_pin']
motor_manual_down_pin = config.CONFIG['motor_manual_down_pin']

motor_max_time = config.CONFIG['motor_safety_stop_after_seconds']
motor_started_at = 0

### SIMULATION
simulate_now = 0 
simulated_now = pytz.timezone(config.CONFIG['timezone']).localize(datetime.datetime.now()).replace(hour=0,minute=0)

motor_up_delta=datetime.timedelta(minutes=config.CONFIG['motor_up_before_sunrise_minutes'])

def start_motor(results,p):
  global state
  global simulated_now
  global motor_started_at
  global client

  logger.info("Starting Motor Process..")

  GPIO.setwarnings(False)

  GPIO.setmode(GPIO.BOARD)
  
  GPIO.setup(top_pin, GPIO.IN)
  GPIO.setup(bottom_pin, GPIO.IN)
  GPIO.setup(motor_manual_up_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(motor_manual_down_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


  GPIO.setup(pin_up, GPIO.OUT)
  GPIO.setup(pin_down, GPIO.OUT)



  GPIO.output(pin_up, 0)
  GPIO.output(pin_down, 0)
  reset_motor()


  logger.info("Subscribing to mqtt")

  state = get_state_from_switches()
  state = 'up'

  motor_started_at = get_now()

  logger.info("Initial Doorstate: " + state)
  while 1:
     results['lastMotorState'] = state

     check_manual_buttons()
     logger.debug("State after check: " + state)

     if state == 'night': 
         check_night()
         if motor_started_at == 0:
            simulated_now = simulated_now + datetime.timedelta(hours=1)

     if state == 'day':
         check_day(results)
         if motor_started_at == 0:
            simulated_now = simulated_now + datetime.timedelta(hours=1)

     if state == 'up':
         motor_up()

     if state == 'down':
         motor_down()
     
     if state == 'error':
         logger.error( "Motor in error state. Exit." )
         exit()
     
     logger.debug("State after everything: " + state)

     # if no motor is active, only check all X seconds
     # if the motor is active check every 0.2 seconds for a stop switch signal
     if motor_started_at == 0:
         time.sleep(1)
     else:
         time.sleep(0.1)

  GPIO.cleanup()
def check_manual_buttons():
    global state
    btn_up_state = GPIO.input(motor_manual_up_pin)
    btn_down_state = GPIO.input(motor_manual_down_pin)

    logger.debug("ButonState: " + str(btn_up_state) + " / " + str(btn_down_state))

    if int(btn_up_state) == 0:
        motor_started_at = get_now()
        state = 'up'
        return

    if int(btn_down_state) == 0:
        motor_started_at = get_now()
        state = 'down'
        return

def on_message(client, userdata, message):
  print("Received message '" + str(message.payload) + "' on topic '" + message.topic + "' with QoS " + str(message.qos))

def check_day(results):
   global state
   global motor_started_at
   motor_started_at = 0

   now = get_now()
   sun=loc.sun(date=now, local=True)

   sunset_time = sun['sunset'].replace(second=0,microsecond=0)
   sleep_time = now.replace(hour=config.CONFIG['sleep_at_hour'],minute=config.CONFIG['sleep_at_minute'], second=0, microsecond=0)
   logger.debug("Now   : " + str(now)) 
   logger.debug("Sunset: " + str(sunset_time))
   logger.debug("Sleep : " + str(sleep_time))
   # close time is sunset or sleep time - whatever is later
   if (sunset_time - sleep_time).total_seconds() > 0:
       close_time = sunset_time + datetime.timedelta(seconds=config.CONFIG['sleep_transition_seconds'], minutes=config.CONFIG['motor_close_added_time_minutes'])
   else:
       close_time = sleep_time + datetime.timedelta(seconds=config.CONFIG['sleep_transition_seconds'], minutes=config.CONFIG['motor_close_added_time_minutes'])


   logger.debug("Close Time is " + str(close_time))
   results['close_time'] = str(close_time)

   if now > close_time:
       logger.debug("Sleeping Time!")
       motor_started_at = now
       state = 'down'

def check_night():
    global state
    global motor_started_at
    motor_started_at = 0

    now = get_now()

    sun=loc.sun(date=now, local=True)

    sunrise_time = sun['sunrise'].replace(second=0,microsecond=0)
    sunset_time = sun['sunset'].replace(second=0,microsecond=0)

    open_time = sunrise_time - motor_up_delta

    logger.debug("Now          : " + str(now))
    logger.debug("Sunrise is at: " + str(sunrise_time))
    logger.debug("Open Time at:  " + str(open_time))
    logger.debug("Now-open_time: " + str((now-sunset_time).total_seconds()))

    if now > open_time and (now - sunset_time).total_seconds() < 0:
        logger.debug("Door Open")
        state = 'up'
        motor_started_at = now

    
def motor_up():
    global state
    GPIO.output(pin_up, 1)
    GPIO.output(pin_down, 0)

    if(GPIO.input(top_pin) == 0):
        state = 'day'
        logger.debug("Top Stop received")
        reset_motor()
    if (get_now() - motor_started_at).total_seconds() > motor_max_time:
        state = 'error'
        logger.error("No Stop Switch signal received in time")
        reset_motor()

def motor_down():
    global state
    GPIO.output(pin_down, 1)
    GPIO.output(pin_up, 0)

    if GPIO.input(bottom_pin) == 0:
        state = 'night'
        logger.debug("Bottom Stop Received")
        reset_motor()
    if motor_started_at == 0: 
        return

    if (get_now() - motor_started_at).total_seconds() > motor_max_time:
        state = 'night'
        logger.error("No Stop Switch signal received in time")
        reset_motor()

def reset_motor():
    GPIO.output(pin_down, 0)
    GPIO.output(pin_up, 0)

def dump_stop_switches():
    logger.debug("STOP BOTTOM: " + str(GPIO.input(bottom_pin)))
    logger.debug("STOP TOP   : " + str(GPIO.input(top_pin)))

# get the current state only by switch
def get_state_from_switches():
    global motor_started_at
    top_state = GPIO.input(top_pin)
    bottom_state = GPIO.input(bottom_pin)

    #if both stop switches are on, go into error state
#    if top_state == 1 and bottom_state == 1:
#        return 'error'

    # none of the stop switches are active - seems we were transitioning. let's pull up to get a determined state
    if top_state == 0 and bottom_state == 0:
        motor_started_at = get_now()
        return 'up'

    if top_state == 1:
        return 'day'

    if bottom_state == 1:
        return 'night'

def get_now():
    if simulate_now: 
        return simulated_now
    return pytz.timezone(config.CONFIG['timezone']).localize(datetime.datetime.now())

if __name__ == '__main__':
  start_motor()

