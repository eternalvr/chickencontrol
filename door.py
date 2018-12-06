import time
import config
import RPi.GPIO as GPIO
def check_door():

    motor_up_pin=13
    motor_down_pin=15

    door_state = "open"
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(motor_up_pin, GPIO.OUT)
    GPIO.setup(motor_down_pin, GPIO.OUT)

    GPIO.output(motor_up_pin, 0)
    GPIO.output(motor_down_pin, 0)

    GPIO.output(motor_down_pin, 1)
    time.sleep(2)


    GPIO.cleanup()

if __name__ == '__main__':
    check_door()
