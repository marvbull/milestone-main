import multiprocessing
import time
import smbus
import RPi.GPIO as GPIO

import i2c
import arduino
from constants import (
    TURNTABLE_ADDR, ROBO_ADDR, M5DIAL_ADDR,
    ROBO_MOVE_A, TURN_MOVE_ASM, TURN_MOVE_SND,
    CMD_STOP, RESP_DONE_ROBO_A, RESP_DONE_TURN_ASM, RESP_DONE_TURN_SND,
    RESP_ERROR
)

bus = smbus.SMBus(1)
NOTAUS_PIN = 17

def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():
        try:
            val = bus.read_byte(M5DIAL_ADDR)
            if val == 1:
                dial_queue.put("start")
        except: pass
        time.sleep(0.5)

def workerRobo(q, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not q.empty():
                cmd = q.get()
                arduino.moveRobo(ROBO_ADDR, cmd)
        time.sleep(0.05)
    finally:
        arduino.moveRobo(ROBO_ADDR, CMD_STOP)

def workerDrehteller(q, shutdown_event):
    try:
        while not shutdown_event.is_set():
            if not q.empty():
                cmd = q.get()
                arduino.moveRobo(TURNTABLE_ADDR, cmd)
        time.sleep(0.05)
    finally:
        arduino.moveRobo(TURNTABLE_ADDR, CMD_STOP)

def workerSafety(shutdown_event):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while not shutdown_event.is_set():
        if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
            shutdown_event.set()
        time.sleep(0.1)
    GPIO.cleanup(NOTAUS_PIN)

def read_status(addr):
    try:
        return bus.read_byte(addr)
    except:
        return None

# --- Hauptprogramm ---
i2c.init_i2c()

if __name__ == "__main__":
    queue_robo = multiprocessing.Queue()
    queue_dreh = multiprocessing.Queue()
    dial_queue = multiprocessing.Queue()
    shutdown_event = multiprocessing.Event()

    procs = [
        multiprocessing.Process(target=workerDial, args=(dial_queue, shutdown_event)),
        multiprocessing.Process(target=workerRobo, args=(queue_robo, shutdown_event)),
        multiprocessing.Process(target=workerDrehteller, args=(queue_dreh, shutdown_event)),
        multiprocessing.Process(target=workerSafety, args=(shutdown_event,))
    ]

    for p in procs:
        p.start()

    try:
        state = "idle"
        stueck = 1

        while not shutdown_event.is_set():
            if state == "idle":
                if not dial_queue.empty() and dial_queue.get() == "start":
                    print("Produktionszyklus gestartet")
                    stueck = 1
                    state = "dial_info"

            elif state == "dial_info":
                try:
                    bus.write_byte(M5DIAL_ADDR, 10 + stueck)
                    state = "turn_asm"
                    queue_dreh.put(TURN_MOVE_ASM)
                    print(f"[{stueck}] → Drehteller ASM gestartet")
                except:
                    shutdown_event.set()

            elif state == "turn_asm":
                r = read_status(TURNTABLE_ADDR)
                if r == RESP_DONE_TURN_ASM:
                    queue_robo.put(ROBO_MOVE_A)
                    print(f"[{stueck}] → Roboter MOVE_A gestartet")
                    state = "robo"

                elif r == RESP_ERROR:
                    print("Fehler vom Drehteller bei ASM")
                    shutdown_event.set()

            elif state == "robo":
                r = read_status(ROBO_ADDR)
                if r == RESP_DONE_ROBO_A:
                    queue_dreh.put(TURN_MOVE_SND)
                    print(f"[{stueck}] → Drehteller SND gestartet")
                    state = "turn_snd"

                elif r == RESP_ERROR:
                    print("Fehler vom Roboter")
                    shutdown_event.set()

            elif state == "turn_snd":
                r = read_status(TURNTABLE_ADDR)
                if r == RESP_DONE_TURN_SND:
                    print(f"[{stueck}] → Stück {stueck} abgeschlossen\n")
                    stueck += 1
                    if stueck > 10:
                        print("Zyklus beendet.")
                        state = "idle"
                    else:
                        state = "dial_info"

                elif r == RESP_ERROR:
                    print("Fehler vom Drehteller bei SND")
                    shutdown_event.set()

            time.sleep(0.1)

    except KeyboardInterrupt:
        shutdown_event.set()

    for p in procs:
        p.terminate()
    for p in procs:
        p.join()
    print("System heruntergefahren.")
