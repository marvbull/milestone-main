from gpiozero import PWMLED
from time import sleep
#import RPi.GPIO as GPIO
#import time

#red= PWMLED(22)
#green = PWMLED(27)
blue = PWMLED(18)

#red.value = 1       #max rot
#green.value = 1   #mittel grün
blue.value = 1      #kein blau

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(18, GPIO.OUT)

#pwm = GPIO.PWM(18, 1000)
#pwm.start(50)

#time.sleep(10)

#pwm.stop()
#GPIO.cleanup()


#print("Setze High")
#GPIO.output(18, GPIO.HIGH)
#time.sleep(10)

#print("Setze Low")
#GPIO.output(18, GPIO.LOW)
#GPIO.cleanup()