
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
    TURN_MOVE_ASM,
    TURN_MOVE_SND,
    CMD_CALIBRATE,
    CMD_STOP,
    RESP_DONE_ROBO_A,
    RESP_DONE_TURN_ASM,
    RESP_DONE_TURN_SND,
    RESP_ERROR
)

bus = smbus.SMBus(1)
NOTAUS_PIN = 17

# --- Arbeiterprozesse ---

def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():
        try:
            response = bus.read_byte(M5DIAL_ADDR)
            if response == 1:
                print("Startsignal empfangen vom M5Dial")
                dial_queue.put("start")
            else:
                print("M5Dial meldet: bereit (Status 0)")
        except Exception as e:
            print("Fehler beim Lesen vom M5Dial:", e)
        time.sleep(1)

def workerDrehteller(queue, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not queue.empty():
                cmd = queue.get()
                print("Drehteller erhält Befehl:", cmd)
                arduino.moveRobo(TURNTABLE_ADDR, cmd)
            time.sleep(0.1)
    finally:
        print("Stoppe Drehteller...")
        try:
            arduino.moveRobo(TURNTABLE_ADDR, CMD_STOP)
        except Exception as e:
            print("Fehler beim STOP an Drehteller:", e)

def workerRobo(queue, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not queue.empty():
                cmd = queue.get()
                print("Roboter erhält Befehl:", cmd)
                arduino.moveRobo(ROBO_ADDR, cmd)
            time.sleep(0.1)
    finally:
        print("Stoppe Roboterarm...")
        try:
            arduino.moveRobo(ROBO_ADDR, CMD_STOP)
        except Exception as e:
            print("Fehler beim STOP an Roboterarm:", e)

def workerSafety(shutdown_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    print("Überwache echten Not-Aus an GPIO17")
    try:
        while not shutdown_event.is_set():
            if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
                print("NOT-AUS ausgelöst")
                shutdown_event.set()
                break
            time.sleep(0.1)
    finally:
        GPIO.cleanup(NOTAUS_PIN)

# --- Hauptablauf ---

i2c.init_i2c()

if __name__ == "__main__":
    queue_robo = multiprocessing.Queue()
    queue_dreh = multiprocessing.Queue()
    dial_queue = multiprocessing.Queue()
    shutdown_event = multiprocessing.Event()

    procs = [
        multiprocessing.Process(target=workerRobo, args=(queue_robo, shutdown_event)),
        multiprocessing.Process(target=workerDrehteller, args=(queue_dreh, shutdown_event)),
        multiprocessing.Process(target=workerDial, args=(dial_queue, shutdown_event)),
        multiprocessing.Process(target=workerSafety, args=(shutdown_event,))
    ]

    for p in procs:
        p.start()

    try:
        while not shutdown_event.is_set():
            if not dial_queue.empty() and dial_queue.get() == "start":
                print("Produktionszyklus gestartet")

                for stueck in range(1, 11):
                    print(f"Verarbeite Stück {stueck}...")

                    try:
                        bus.write_byte(M5DIAL_ADDR, 10 + stueck)
                    except Exception as e:
                        print("I2C Fehler M5Dial:", e)
                        shutdown_event.set()
                        break

                    # Drehteller: Position ASM (30)
                    queue_dreh.put(TURN_MOVE_ASM)
                    while not shutdown_event.is_set():
                        try:
                            r = bus.read_byte(TURNTABLE_ADDR)
                            if r == RESP_DONE_TURN_ASM:
                                print("→ Drehteller ASM ok")
                                break
                            elif r == RESP_ERROR:
                                print("Fehler vom Drehteller")
                                shutdown_event.set()
                                break
                        except: pass
                        time.sleep(20)

                    if shutdown_event.is_set(): break

                    # Roboter: MOVE_A
                    queue_robo.put(ROBO_MOVE_A)
                    while not shutdown_event.is_set():
                        try:
                            r = bus.read_byte(ROBO_ADDR)
                            if r == RESP_DONE_ROBO_A:
                                print("→ Roboter MOVE_A ok")
                                break
                            elif r == RESP_ERROR:
                                print("Fehler vom Roboter")
                                shutdown_event.set()
                                break
                        except: pass
                        time.sleep(20)

                    if shutdown_event.is_set(): break

                    # Drehteller: Position SND (40)
                    queue_dreh.put(TURN_MOVE_SND)
                    while not shutdown_event.is_set():
                        try:
                            r = bus.read_byte(TURNTABLE_ADDR)
                            if r == RESP_DONE_TURN_SND:
                                print("→ Drehteller SND ok")
                                break
                            elif r == RESP_ERROR:
                                print("Fehler vom Drehteller")
                                shutdown_event.set()
                                break
                        except: pass
                        time.sleep(20)

            time.sleep(20)

    except KeyboardInterrupt:
        shutdown_event.set()

    print("Beende Prozesse...")
    for p in procs:
        p.terminate()
    for p in procs:
        p.join()
    print("System heruntergefahren.")
