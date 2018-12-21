import paho.mqtt.client as mqtt
import logging
import config

client = 1
logger = logging.getLogger()

def on_connect(client, userdata, flags, rc):
    logger.info("Connected to MQTT: " + str(rc) + str(userdata))
    

def initialize_mqtt(name=""):
  global client
  client = mqtt.Client(config.CONFIG['mqtt_client'] + name)
  client.enable_logger()
  client.on_connect = on_connect
  client.username_pw_set(config.CONFIG['mqtt_user'], config.CONFIG['mqtt_password'])
  try:
      client.connect(config.CONFIG['mqtt_host'])
  except:
      logger.error("Could not connect to MQTT..")
  client.loop_start()

  return client
def get_client():
    return client
