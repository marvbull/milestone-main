from gpiozero import PWMLED
from time import sleep

red= PWMLED(22)
green = PWMLED(27)
blue = PWMLED(17)

red.value = 1       #max rot
green.value = 0   #mittel grün
blue.value = 0      #kein blau