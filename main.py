import multiprocessing
import i2c
import arduino
import time
import os
import RPi.GPIO as GPIO

# GPIO-Pin für Not-Aus-Schalter (z. B. Pin 17 = GPIO17)
NOTAUS_PIN = 17

def i2c_worker():
    i2c.init_i2c()
    while True:
        status = arduino.sende_befehl(0x08, 1)  # Beispiel: moveA
        print("I2C Status:", status)
        time.sleep(2)

def sicherheit_worker(event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while True:
        if GPIO.input(NOTAUS_PIN) == GPIO.LOW:  # Taster gedrückt
            print("NOT-AUS aktiviert!")
            event.set()  # Signal an anderen Prozess
            break
        time.sleep(0.1)

if __name__ == "__main__":
    shutdown_event = multiprocessing.Event()

    p1 = multiprocessing.Process(target=i2c_worker)
    p2 = multiprocessing.Process(target=sicherheit_worker, args=(shutdown_event,))

    p1.start()
    p2.start()

    while not shutdown_event.is_set():
        time.sleep(0.5)

    print("Beende Prozesse wegen Sicherheitsereignis...")
    p1.terminate()
    p2.terminate()
    p1.join()
    p2.join()
    i2c.close_i2c()
    print("System sicher beendet.")
