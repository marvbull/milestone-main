
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

# Statusflags
pause_flag = multiprocessing.Value('b', False)

def workerDial(dial_queue, shutdown_event):
    while not shutdown_event.is_set():
            if pause_flag.value:
                print("Pause aktiv – warte auf CONTINUE...")
                time.sleep(1)
                continue

        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == DIAL_START:
                print("Startsignal vom M5Dial empfangen")
                dial_queue.put("start")
            else:
                print(f"M5Dial Status: {status}")
        except Exception as e:
            print("Fehler beim Lesen vom M5Dial:", e)
        time.sleep(1)

def workerDrehteller(queue, shutdown_event):
    while not shutdown_event.is_set():
            if pause_flag.value:
                print("Pause aktiv – warte auf CONTINUE...")
                time.sleep(1)
                continue

        if not queue.empty():
            cmd = queue.get()
            arduino.moveRobo(TURNTABLE_ADDR, cmd)
        time.sleep(0.1)

def workerRobo(queue, shutdown_event):
    while not shutdown_event.is_set():
            if pause_flag.value:
                print("Pause aktiv – warte auf CONTINUE...")
                time.sleep(1)
                continue

        if not queue.empty():
            cmd = queue.get()
            arduino.moveRobo(ROBO_ADDR, cmd)
        time.sleep(0.1)

def workerSafety(shutdown_event, pause_flag):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while not shutdown_event.is_set():
            if pause_flag.value:
                print("Pause aktiv – warte auf CONTINUE...")
                time.sleep(1)
                continue

        if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
            print("NOTAUS erkannt! System pausiert.")
            pause_flag.value = True
        time.sleep(0.1)
    GPIO.cleanup(NOTAUS_PIN)

def wait_for_response(addr, expected_response, label):
    while True:
        try:
            r = bus.read_byte(addr)
            if r == expected_response:
                print(f"{label} abgeschlossen.")
                return True
            elif r == RESP_ERROR:
                print(f"{label} meldet Fehler!")
                return False
        except:
            pass
        time.sleep(0.2)

def wait_until_resumed(pause_flag):
    while pause_flag.value:
        print("System pausiert... Warte auf CONTINUE (Taste oder I2C)")
        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == CMD_CONTINUE:
                pause_flag.value = False
                print("Fortsetzung bestätigt.")
        except:
            pass
        time.sleep(0.5)

# Initialisierung
i2c.init_i2c()


GPIO.setmode(GPIO.BCM)
GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
print("Überprüfe Not-Aus beim Start...")

if GPIO.input(NOTAUS_PIN) == GPIO.HIGH:
    print("NOT-AUS ist AKTIV – starte im PAUSE-Modus")
    pause_flag.value = True
else:
    print("NOT-AUS nicht aktiv – sende CONTINUE an Geräte")
    try:
        arduino.moveRobo(ROBO_ADDR, CMD_CONTINUE)
        arduino.moveRobo(TURNTABLE_ADDR, CMD_CONTINUE)
    except Exception as e:
        print("Fehler beim CONTINUE-Senden:", e)
    pause_flag.value = False


if __name__ == "__main__":
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
                print("Pause aktiv – warte auf CONTINUE...")
                time.sleep(1)
                continue

            if not dial_queue.empty() and dial_queue.get() == "start":
                print("→ Produktionsstart erkannt")

                for stueck in range(1, 11):
                    print(f"Bearbeite Stück {stueck}...")
                    wait_until_resumed(pause_flag)

                    # Sende Stückzahl an M5Dial
                    try:
                        bus.write_byte(M5DIAL_ADDR, 10 + stueck)
                    except Exception as e:
                        print("Fehler beim Schreiben an M5Dial:", e)
                        break

                    # 1. ASM (30)
                    queue_dreh.put(TURN_MOVE_ASM)
                    if not wait_for_response(TURNTABLE_ADDR, RESP_DONE_TURN_ASM, "Drehteller ASM"):
                        break

                    wait_until_resumed(pause_flag)

                    # 2. Roboter MOVE_A
                    queue_robo.put(ROBO_MOVE_A)
                    if not wait_for_response(ROBO_ADDR, RESP_DONE_ROBO_A, "Roboter MOVE_A"):
                        break

                    wait_until_resumed(pause_flag)

                    # 3. SND (40)
                    queue_dreh.put(TURN_MOVE_SND)
                    if not wait_for_response(TURNTABLE_ADDR, RESP_DONE_TURN_SND, "Drehteller SND"):
                        break

            time.sleep(0.2)

    except KeyboardInterrupt:
        shutdown_event.set()

    print("Beende Prozesse...")
    for p in procs:
        p.terminate()
    for p in procs:
        p.join()
    print("System vollständig heruntergefahren.")



def workerControl(bus, pause_flag, shutdown_event):
    while not shutdown_event.is_set():
        try:
            for addr in [ROBO_ADDR, TURNTABLE_ADDR]:
                try:
                    value = bus.read_byte(addr)
                    if value == CMD_STOP:
                        print(f"STOP erkannt von Adresse {hex(addr)} – Pause aktiviert")
                        pause_flag.value = True
                    elif value == CMD_CONTINUE:
                        print(f"CONTINUE erkannt von Adresse {hex(addr)} – Pause beendet")
                        pause_flag.value = False
                except: pass
            time.sleep(0.5)
        except Exception as e:
            print("Fehler im Control-Worker:", e)
