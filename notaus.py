import RPi.GPIO as GPIO
import time

# GPIO-Pins definieren
OUTPUT_PIN = 17  # Pin, der den Strom liefert
NOTAUS_PIN = 27   # Pin, der den Strom empfangen soll
TUER_PIN = 22  # Pin für den Türkontakt 
TUER_PIN2 = 24  # Pin für den Türkontakt (zweite Tür)
KLAPPE_PIN = 23  # Pin für die Klappenkontakt 
KLAPPE_PIN2 = 25  # Pin für die Klappenkontakt (zweite Klappe)


def workerSafety(shutdown_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(OUTPUT_PIN, GPIO.OUT)
    GPIO.setup(NOTAUS_PIN, GPIO.IN)
    GPIO.setup(TUER_PIN, GPIO.IN)  
    GPIO.setup(TUER_PIN2, GPIO.IN)
    GPIO.setup(KLAPPE_PIN, GPIO.IN)
    GPIO.setup(KLAPPE_PIN2, GPIO.IN)

    GPIO.output(OUTPUT_PIN, GPIO.HIGH)
    time.sleep(1)
    print("Überwache echten Not-Aus an GPIO17")

    try:
        while True:
            while not shutdown_event.is_set():
                if GPIO.input(NOTAUS_PIN) != GPIO.HIGH:
                    print("Not-Aus AUSGELÖST (Taste gedrückt)")
                    shutdown_event.set()
                    break
                elif GPIO.input(TUER_PIN) != GPIO.HIGH:
                    print("Türe1 offen")
                    shutdown_event.set()
                    break
                elif GPIO.input(TUER_PIN2) != GPIO.HIGH:
                    print("Türe2 offen")
                    shutdown_event.set()
                    break
                elif GPIO.input(KLAPPE_PIN) != GPIO.HIGH:
                    print("Klappe offen")
                    shutdown_event.set()
                    break
                elif GPIO.input(KLAPPE_PIN2) != GPIO.HIGH:
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
        #print("Shutdown-Event gesetzt")
        pass





# Funktion, um den Notaus-Mechanismus zu prüfen
def notaus_pruefen():
    # GPIO Setup
    GPIO.setmode(GPIO.BCM)  # Pin-Nummern im BCM-Modus
    GPIO.setup(OUTPUT_PIN, GPIO.OUT)  # Pin für Ausgang (Strom geben)
    GPIO.setup(NOTAUS_PIN, GPIO.IN)   # Pin für Eingang (Strom empfangen)

    # Strom auf OUTPUT_PIN geben
    GPIO.output(OUTPUT_PIN, GPIO.HIGH)
    time.sleep(1)  # Eine Sekunde warten, um sicherzustellen, dass der Strom fließt

    # Überprüfen, ob auf INPUT_PIN Strom ankommt
    if GPIO.input(INPUT_PIN) == GPIO.HIGH:
        print("Strom an INPUT_PIN erkannt. Alles in Ordnung.")
    else:
        print("Kein Strom an INPUT_PIN! Not-Aus ausgelöst.")

    # Strom auf OUTPUT_PIN abschalten
    GPIO.output(OUTPUT_PIN, GPIO.LOW)

#try:
 #   while True:
#        notaus_pruefen()
 #       time.sleep(5)  # Alle 5 Sekunden die Überprüfung wiederholen

#except KeyboardInterrupt:
 #   print("Programm durch Benutzer unterbrochen.")
#finally:
#    GPIO.cleanup()  # Aufräumen der GPIO-Konfiguration beim Beenden

workerSafety(shutdown_event)