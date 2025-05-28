import multiprocessing
import time
import os
import RPi.GPIO as GPIO

import i2c
import arduino
import constants

# Prozess: Eingabe vom M5Dial simulieren
def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():  # Solange kein Not-Aus
        print("Warte auf Startsignal vom M5Dial...")
        time.sleep(5)                   # Simulation: Startsignal alle 5 Sekunden
        print("Startsignal empfangen")
        dial_queue.put("start")         # "start" wird an Hauptprozess übermittelt
        time.sleep(10)                  # Warten, damit nicht mehrfach gestartet wird

# Prozess: Drehteller-Befehle empfangen und ausführen
def workerDrehteller(queue, shutdown_event):
    while not shutdown_event.is_set():
        if not queue.empty():                      # Gibt es einen neuen Befehl?
            befehl = queue.get()                   # Befehl abrufen
            print("Drehteller erhält Befehl:", befehl)
            arduino.moveRobo(0x09, befehl)         # I2C-Adresse des Drehtellers: 0x09
            print("Drehteller fertig")             # Rückmeldung
        time.sleep(0.1)                            # Kleine Pause zur CPU-Entlastung

# Prozess: Roboterarm-Befehle empfangen und ausführen
def workerRobo(queue, shutdown_event):
    while not shutdown_event.is_set():
        if not queue.empty():                      # Gibt es einen neuen Befehl?
            befehl = queue.get()                   # Befehl abrufen
            print("Roboterarm erhält Befehl:", befehl)
            arduino.moveRobo(0x08, befehl)         # I2C-Adresse des Roboterarms: 0x08
            print("Roboterarm fertig")             # Rückmeldung
        time.sleep(0.1)

# Prozess: Not-Aus überwachen (hier simuliert)
def workerSafety(shutdown_event):
    while True:
        time.sleep(30)                             # Simulation: Not-Aus nach 30 Sekunden
        print("Not-Aus ausgelöst")
        shutdown_event.set()                       # Signal an alle Prozesse zum Stoppen
        break
    
i2c.init_i2c()  # ← ganz wichtig: das muss VORHER kommen!

if __name__ == "__main__":
    # Queues zur Kommunikation mit den Prozessen
    queue_robo = multiprocessing.Queue()           # Befehle für Roboter
    queue_dreh = multiprocessing.Queue()           # Befehle für Drehteller
    dial_queue = multiprocessing.Queue()           # Startsignal vom M5Dial
    shutdown_event = multiprocessing.Event()       # Globales Event für Not-Aus

    # Prozesse erstellen
    p_robo = multiprocessing.Process(target=workerRobo, args=(queue_robo, shutdown_event))
    p_dreh = multiprocessing.Process(target=workerDrehteller, args=(queue_dreh, shutdown_event))
    p_dial = multiprocessing.Process(target=workerDial, args=(dial_queue, shutdown_event))
    p_safety = multiprocessing.Process(target=workerSafety, args=(shutdown_event,))

    # Prozesse starten
    p_robo.start()
    p_dreh.start()
    p_dial.start()
    p_safety.start()

    try:
        # Ablaufsteuerung im Hauptprozess
        while not shutdown_event.is_set():
            if not dial_queue.empty():                     # Wurde Startsignal vom Dial empfangen?
                signal = dial_queue.get()                  # Signal auslesen
                if signal == "start":
                    print("Prozess gestartet")

                    queue_dreh.put(1)                      # Drehteller-Befehl senden
                    time.sleep(20)                          # Kurze Wartezeit, damit Reihenfolge stimmt

                    queue_robo.put(1)                      # Roboter-Befehl senden

            time.sleep(0.2)                                # Entlastung Hauptloop

    except KeyboardInterrupt:
        shutdown_event.set()                               # Bei STRG+C Not-Aus setzen

    print("Stoppe alle Prozesse...")

    # Alle Prozesse ordentlich beenden
    p_robo.terminate()
    p_dreh.terminate()
    p_dial.terminate()
    p_safety.terminate()

    p_robo.join()
    p_dreh.join()
    p_dial.join()
    p_safety.join()

    print("System beendet")

