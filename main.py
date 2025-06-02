import multiprocessing
import time
import smbus
import RPi.GPIO as GPIO

import i2c
import arduino
from constants import (
    TURNTABLE_ADDR,
    ROBO_ADDR,
    M5DIAL_ADDR,
    ROBO_MOVE_A,
    ROBO_MOVE_B,
    TURN_MOVE_ASM,
    TURN_MOVE_SND,
    CMD_CALIBRATE,
    CMD_STOP,
    RESP_DONE_ROBO_A,
    RESP_DONE_ROBO_B,
    RESP_DONE_TURN_ASM,
    RESP_DONE_TURN_SND,
    RESP_ERROR
)

bus = smbus.SMBus(1)  # I2C-Bus
NOTAUS_PIN = 17       # GPIO17 (physikalisch Pin 11)

# Dial-Prozess: Simuliert Startsignal
def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():
        print("Warte auf Startsignal vom M5Dial")
        time.sleep(5)
        print("Startsignal empfangen")
        dial_queue.put("start")
        time.sleep(10)

# Drehteller-Prozess
def workerDrehteller(queue, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not queue.empty():
                befehl = queue.get()
                print("Drehteller erhält Befehl:", befehl)
                arduino.moveRobo(TURNTABLE_ADDR, befehl)
                print("Drehteller-Befehl ausgeführt")
            time.sleep(0.1)
    finally:
        print("Not-Aus erkannt - sende STOP an Drehteller")
        try:
            arduino.moveRobo(TURNTABLE_ADDR, CMD_STOP)
        except Exception as e:
            print(f"Fehler beim STOP an Drehteller: {e}")

# Roboter-Prozess
def workerRobo(queue, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not queue.empty():
                befehl = queue.get()
                print("Roboterarm erhält Befehl:", befehl)
                arduino.moveRobo(ROBO_ADDR, befehl)
                print("Roboterarm-Befehl ausgeführt")
            time.sleep(0.1)
    finally:
        print("Not-Aus erkannt - sende STOP an Roboterarm")
        try:
            arduino.moveRobo(ROBO_ADDR, CMD_STOP)
        except Exception as e:
            print(f"Fehler beim STOP an Roboterarm: {e}")

# ECHTER Not-Aus an GPIO17
def workerSafety(shutdown_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    print("Überwache echten Not-Aus an GPIO17")

    try:
        while not shutdown_event.is_set():
            if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
                print("Not-Aus AUSGELÖST (Taste gedrückt)")
                shutdown_event.set()
                break
            time.sleep(0.1)
    finally:
        GPIO.cleanup(NOTAUS_PIN)

# I2C initialisieren
i2c.init_i2c()

if __name__ == "__main__":
    queue_robo = multiprocessing.Queue()
    queue_dreh = multiprocessing.Queue()
    dial_queue = multiprocessing.Queue()
    shutdown_event = multiprocessing.Event()

    p_robo = multiprocessing.Process(target=workerRobo, args=(queue_robo, shutdown_event))
    p_dreh = multiprocessing.Process(target=workerDrehteller, args=(queue_dreh, shutdown_event))
    p_dial = multiprocessing.Process(target=workerDial, args=(dial_queue, shutdown_event))
    p_safety = multiprocessing.Process(target=workerSafety, args=(shutdown_event,))

    p_robo.start()
    p_dreh.start()
    p_dial.start()
    p_safety.start()

    try:
        while not shutdown_event.is_set():
            if not dial_queue.empty():
                signal = dial_queue.get()
                if signal == "start":
                    print("Prozess gestartet")

                    # Schritt 1: Drehteller ASM
                    queue_dreh.put(TURN_MOVE_ASM)
                    print("Warte auf Rückmeldung vom Drehteller (ASM)...")

                    while not shutdown_event.is_set():
                        try:
                            response = bus.read_byte(TURNTABLE_ADDR)
                            if response == RESP_DONE_TURN_ASM:
                                print("Drehteller ASM abgeschlossen.")
                                break
                            elif response == RESP_ERROR:
                                print("Fehler vom Drehteller!")
                                shutdown_event.set()
                                break
                        except Exception as e:
                            print(f"I2C-Lesefehler Drehteller: {e}")
                        time.sleep(0.2)

                    if shutdown_event.is_set():
                        break

                    # Schritt 2: Roboter MOVE_A
                    queue_robo.put(ROBO_MOVE_A)
                    print("Warte auf Rückmeldung vom Roboter...")

                    while not shutdown_event.is_set():
                        try:
                            response = bus.read_byte(ROBO_ADDR)
                            if response == RESP_DONE_ROBO_A:
                                print("Roboter MOVE_A abgeschlossen.")
                                break
                            elif response == RESP_ERROR:
                                print("Fehler vom Roboter!")
                                shutdown_event.set()
                                break
                        except Exception as e:
                            print(f"I2C-Lesefehler Roboter: {e}")
                        time.sleep(0.2)

                    if shutdown_event.is_set():
                        break

                    # Schritt 3: Drehteller SND
                    queue_dreh.put(TURN_MOVE_SND)
                    print("TURN_MOVE_SND an Drehteller gesendet. Warte auf Bestätigung...")

                    while not shutdown_event.is_set():
                        try:
                            response = bus.read_byte(TURNTABLE_ADDR)
                            if response == RESP_DONE_TURN_SND:
                                print("Drehteller meldet SND abgeschlossen.")
                                break
                            elif response == RESP_ERROR:
                                print("Fehler beim SND vom Drehteller!")
                                shutdown_event.set()
                                break
                        except Exception as e:
                            print(f"I2C-Lesefehler Drehteller (SND): {e}")
                        time.sleep(0.2)

            time.sleep(0.2)

    except KeyboardInterrupt:
        shutdown_event.set()

    print("Stoppe alle Prozesse...")

    # Prozesse beenden
    p_robo.terminate()
    p_dreh.terminate()
    p_dial.terminate()
    p_safety.terminate()

    p_robo.join()
    p_dreh.join()
    p_dial.join()
    p_safety.join()

    print("System beendet.")
