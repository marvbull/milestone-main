import RPi.GPIO as GPIO
import time

# GPIO-Pins definieren
OUTPUT_PIN = 17  # Pin, der den Strom liefert
NOTAUS_PIN = 27   # Pin, der den Strom empfangen soll
TUER_PIN = 22  # Pin für den Türkontakt 
KLAPPE_PIN = 23  # Pin für die Klappenkontakt 


def workerSafety(shutdown_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(OUTPUT_PIN, GPIO.OUT)
    GPIO.setup(NOTAUS_PIN, GPIO.IN)
    GPIO.setup(TUER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
    GPIO.setup(KLAPPE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.output(OUTPUT_PIN, GPIO.HIGH)

    time.sleep(1)
    print("Überwache echten Not-Aus an GPIO17")

    try:
        while True:
            while not shutdown_event.is_set():
                if GPIO.input(NOTAUS_PIN) != GPIO.HIGH or GPIO.input(TUER_PIN) != GPIO.HIGH != GPIO.HIGH or GPIO.input(KLAPPE_PIN) != GPIO.HIGH != GPIO.HIGH:
                    #print("Not-Aus AUSGELÖST")
                    shutdown_event.set()
                    break
                #elif GPIO.input(TUER_PIN) != GPIO.HIGH:     # später als OR
                    print("Türe offen")
                    shutdown_event.set()
                    break
                #elif GPIO.input(TUER_PIN2) != GPIO.HIGH:
                    print("Türe offen")
                    shutdown_event.set()
                    break
                #elif GPIO.input(KLAPPE_PIN) != GPIO.HIGH:
                    print("Klappe offen")
                    shutdown_event.set()
                    break
                #elif GPIO.input(KLAPPE_PIN2) != GPIO.HIGH:
                    print("Klappe offen")
                    shutdown_event.set()
                    break

                else:
                    print("Nichts ausgelöst")
                time.sleep(0.1)
                
    except KeyboardInterrupt:       #im richtigen Code nicht benötigt
        print("Programm durch Benutzer unterbrochen.")

    finally:
        GPIO.cleanup()  # Aufräumen der GPIO-Konfiguration beim Beenden

class shutdown_event():
    def is_set():
        # Hier sollte die Logik implementiert werden, um den Shutdown-Status zu überprüfen
        return False
    def set():
        # Hier sollte die Logik implementiert werden, um den Shutdown-Status zu setzen
        print("Shutdown-Event gesetzt")
        pass





workerSafety(shutdown_event)