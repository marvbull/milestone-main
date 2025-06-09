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
    CMD_CONTINUE,
    DIAL_START,
    RESP_DONE_ROBO_A,
    RESP_DONE_TURN_ASM,
    RESP_DONE_TURN_SND,
    RESP_ERROR
)

bus = smbus.SMBus(1)
NOTAUS_PIN = 17
pause_flag = multiprocessing.Value('b', False)

def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():
        if pause_flag.value:
            time.sleep(1)
            continue
        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == DIAL_START:
                print("[M5Dial] Startsignal empfangen")
                dial_queue.put("start")
            else:
                print(f"[M5Dial] Status: {status}")
        except Exception as e:
            print("[M5Dial] Fehler beim Lesen:", e)
        time.sleep(1)

def workerDrehteller(queue, shutdown_event):
    while not shutdown_event.is_set():
        if pause_flag.value:
            time.sleep(1)
            continue
        if not queue.empty():
            cmd = queue.get()
            print(f"[Drehteller] Sende Befehl: {cmd}")
            arduino.moveRobo(TURNTABLE_ADDR, cmd)
        time.sleep(0.1)

def workerRobo(queue, shutdown_event):
    while not shutdown_event.is_set():
        if pause_flag.value:
            time.sleep(1)
            continue
        if not queue.empty():
            cmd = queue.get()
            print(f"[Roboter] Sende Befehl: {cmd}")
            arduino.moveRobo(ROBO_ADDR, cmd)
        time.sleep(0.1)

def workerSafety(shutdown_event, pause_flag):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while not shutdown_event.is_set():
        if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
            print("[Safety] NOT-AUS erkannt – System pausiert")
            pause_flag.value = True
        time.sleep(0.1)
    GPIO.cleanup(NOTAUS_PIN)

def wait_for_response(addr, expected_response, label):
    while True:
        try:
            r = bus.read_byte(addr)
            print(f"[{label}] Antwort von {hex(addr)}: {r}")
            if r == expected_response:
                print(f"[{label}] abgeschlossen.")
                return True
            elif r == RESP_ERROR:
                print(f"[{label}] Fehler gemeldet!")
                return False
        except:
            pass
        time.sleep(0.2)

def wait_until_resumed():
    while pause_flag.value:
        print("[System] Pause aktiv... warte auf CONTINUE")
        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == CMD_CONTINUE:
                pause_flag.value = False
                print("[System] Fortsetzung erkannt")
        except:
            pass
        time.sleep(0.5)

def init_safety():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
        print("[Init] NOT-AUS aktiv – starte in Pause")
        pause_flag.value = True
    else:
        print("[Init] NOT-AUS nicht aktiv – sende CONTINUE")
        try:
            arduino.moveRobo(ROBO_ADDR, CMD_CONTINUE)
            arduino.moveRobo(TURNTABLE_ADDR, CMD_CONTINUE)
        except Exception as e:
            print("[Init] CONTINUE-Senden fehlgeschlagen:", e)
        pause_flag.value = False

def main():
    i2c.init_i2c()
    init_safety()

    queue_robo = multiprocessing.Queue()
    queue_dreh = multiprocessing.Queue()
    dial_queue = multiprocessing.Queue()
    shutdown_event = multiprocessing.Event()

    procs = [
        multiprocessing.Process(target=workerRobo, args=(queue_robo, shutdown_event)),
        multiprocessing.Process(target=workerDrehteller, args=(queue_dreh, shutdown_event)),
        multiprocessing.Process(target=workerDial, args=(dial_queue, shutdown_event)),
        multiprocessing.Process(target=workerSafety, args=(shutdown_event, pause_flag))
    ]

    for p in procs:
        p.start()

    try:
        while not shutdown_event.is_set():
            if pause_flag.value:
                time.sleep(1)
                continue

            if not dial_queue.empty() and dial_queue.get() == "start":
                print("[System] → Produktionsstart erkannt")

                for stueck in range(1, 11):
                    print(f"[System] Bearbeite Stück {stueck}...")
                    wait_until_resumed()

                    # 1. ASM
                    queue_dreh.put(TURN_MOVE_ASM)
                    if not wait_for_response(TURNTABLE_ADDR, RESP_DONE_TURN_ASM, "Drehteller ASM"):
                        break

                    wait_until_resumed()

                    # 2. Roboter
                    queue_robo.put(ROBO_MOVE_A)
                    if not wait_for_response(ROBO_ADDR, RESP_DONE_ROBO_A, "Roboter MOVE_A"):
                        break

                    wait_until_resumed()

                    # 3. SND
                    queue_dreh.put(TURN_MOVE_SND)
                    if not wait_for_response(TURNTABLE_ADDR, RESP_DONE_TURN_SND, "Drehteller SND"):
                        break

            time.sleep(0.2)

    except KeyboardInterrupt:
        shutdown_event.set()

    print("[System] Beende Prozesse...")
    for p in procs:
        p.terminate()
    for p in procs:
        p.join()
    print("[System] Vollständig heruntergefahren.")

if __name__ == "__main__":
    main()
