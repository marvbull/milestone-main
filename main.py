#!/usr/bin/env python3
import smbus
import time
import RPi.GPIO as GPIO
import threading

# Konstanten
TURNTABLE_ADDR = 0x09
ROBO_ADDR = 0x08
M5DIAL_ADDR = 0x10

TURN_MOVE_ASM = 30
TURN_MOVE_SND = 40
ROBO_MOVE_A = 10

CMD_CONTINUE = 98
CMD_STOP = 99
CMD_CAL = 90
DIAL_START = 1
DIAL_STOP = 2
DONE_1 = 105
DONE_2 = 115
DONE_3 = 125

NOTAUS_PIN = 17
bus = smbus.SMBus(1)

pause_flag = threading.Event()
start_flag = threading.Event()
bus_lock = threading.Lock()

def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def is_notaus_active():
    return GPIO.input(NOTAUS_PIN) == GPIO.HIGH

def send_command(addr, cmd, name):
    with bus_lock:
        print(f"[{name}] → Sende Befehl {cmd} an {hex(addr)}")
        try:
            bus.write_byte(addr, cmd)
        except Exception as e:
            print(f"[{name}] Fehler beim Senden: {e}")

def wait_for_idle(addr, idle_value, name):
    print(f"[{name}] Warte auf Status {idle_value} von {hex(addr)}...")
    while True:
        if pause_flag.is_set():
            print(f"[{name}] → Pause erkannt – warte...")
            time.sleep(1)
            continue
        try:
            with bus_lock:
                status = bus.read_byte(addr)
            print(f"[{name}] Status: {status}")
            if status == idle_value:
                print(f"[{name}] abgeschlossen.")
                return
        except Exception as e:
            print(f"[{name}] Fehler beim Lesen: {e}")
        time.sleep(0.5)

def monitor_m5dial():
    while True:
        try:
            with bus_lock:
                status = bus.read_byte(M5DIAL_ADDR)

            if status == DIAL_STOP and not pause_flag.is_set():
                print("[M5Dial] STOP erkannt – pausiere System")
                pause_flag.set()
                send_command(ROBO_ADDR, CMD_STOP, "Roboter")
                send_command(TURNTABLE_ADDR, CMD_STOP, "Drehteller")
                send_command(M5DIAL_ADDR, CMD_CONTINUE, "M5Dial (Bestätigung)")

            elif status == CMD_CONTINUE and pause_flag.is_set():
                print("[M5Dial] CONTINUE erkannt – fortsetzen")
                pause_flag.clear()
                send_command(ROBO_ADDR, CMD_CONTINUE, "Roboter")
                send_command(TURNTABLE_ADDR, CMD_CONTINUE, "Drehteller")
                time.sleep(1)
                send_command(ROBO_ADDR, CMD_CAL, "Roboter")
                send_command(TURNTABLE_ADDR, CMD_CAL, "Drehteller")

            elif status == DIAL_START and not start_flag.is_set():
                print("[M5Dial] START erkannt – Ablauf starten")
                start_flag.set()

        except Exception as e:
            print("[M5Dial] Fehler:", e)

        time.sleep(0.5)

def monitor_console():
    while True:
        cmd = input(">> ").strip().lower()
        if cmd == "stop":
            print("[Console] STOP erkannt")
            pause_flag.set()
            send_command(ROBO_ADDR, CMD_STOP, "Roboter")
            send_command(TURNTABLE_ADDR, CMD_STOP, "Drehteller")
        elif cmd == "cont":
            print("[Console] CONTINUE erkannt")
            pause_flag.clear()
            send_command(ROBO_ADDR, CMD_CONTINUE, "Roboter")
            send_command(TURNTABLE_ADDR, CMD_CONTINUE, "Drehteller")
        elif cmd == "cal":
            print("[Console] KALIBRIERUNG")
            send_command(ROBO_ADDR, CMD_CAL, "Roboter")
            send_command(TURNTABLE_ADDR, CMD_CAL, "Drehteller")
        else:
            print("[Console] Unbekannter Befehl:", cmd)

def main():
    init_gpio()

    if is_notaus_active():
        print("[Init] NOT-AUS aktiv – warte auf CONTINUE")
        pause_flag.set()
    else:
        print("[Init] NOT-AUS nicht aktiv – sende CONTINUE")
        send_command(ROBO_ADDR, CMD_CONTINUE, "Roboter")
        send_command(TURNTABLE_ADDR, CMD_CONTINUE, "Drehteller")
        time.sleep(1)
        send_command(ROBO_ADDR, CMD_CAL, "Roboter")
        send_command(TURNTABLE_ADDR, CMD_CAL, "Drehteller")

    # Hintergrundthreads starten
    threading.Thread(target=monitor_m5dial, daemon=True).start()
    threading.Thread(target=monitor_console, daemon=True).start()

    print("[System] Warte auf Startsignal vom M5Dial...")

    while True:
        try:
            if start_flag.is_set() and not pause_flag.is_set():
                print("[System] Ablauf beginnt...")
                start_flag.clear()

                for stueck in range(1, 11):
                    if pause_flag.is_set(): break

                    print(f"[System] Bearbeite Stück {stueck}")

                    send_command(TURNTABLE_ADDR, TURN_MOVE_ASM, "Drehteller ASM")
                    wait_for_idle(TURNTABLE_ADDR, DONE_1, "Drehteller ASM")

                    send_command(ROBO_ADDR, ROBO_MOVE_A + (stueck - 1), "Roboter MOVE_A")
                    wait_for_idle(ROBO_ADDR, DONE_2, "Roboter MOVE_A")

                    send_command(TURNTABLE_ADDR, TURN_MOVE_SND, "Drehteller SND")
                    wait_for_idle(TURNTABLE_ADDR, DONE_3, "Drehteller SND")

                print("[System] Ablauf abgeschlossen.")

        except KeyboardInterrupt:
            print("[System] Beendet durch Nutzer.")
            break
        except Exception as e:
            print("[System] Fehler:", e)

        time.sleep(0.5)

    GPIO.cleanup()

if __name__ == "__main__":
    main()
