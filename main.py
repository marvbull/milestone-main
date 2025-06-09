import smbus
import time
import RPi.GPIO as GPIO

# Konstanten
TURNTABLE_ADDR = 0x08
ROBO_ADDR = 0x09
M5DIAL_ADDR = 0x10

TURN_MOVE_ASM = 30
TURN_MOVE_SND = 40
ROBO_MOVE_A = 10

CMD_CONTINUE = 98
DIAL_START = 1
ROBO_IDLE = 105
TURN_IDLE = 125

NOTAUS_PIN = 17
bus = smbus.SMBus(1)

def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NOTAUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def is_notaus_active():
    return GPIO.input(NOTAUS_PIN) == GPIO.HIGH

def send_command(addr, cmd, name):
    print(f"[{name}] Sende Befehl {cmd} an {hex(addr)}")
    try:
        bus.write_byte(addr, cmd)
    except Exception as e:
        print(f"[{name}] Fehler beim Senden: {e}")

def wait_for_idle(addr, idle_value, name):
    print(f"[{name}] Warte auf Status {idle_value} von {hex(addr)}...")
    while True:
        try:
            status = bus.read_byte(addr)
            print(f"[{name}] Status: {status}")
            if status == idle_value:
                print(f"[{name}] abgeschlossen.")
                return
        except Exception as e:
            print(f"[{name}] Fehler beim Lesen: {e}")
        time.sleep(0.2)

def wait_for_continue():
    print("[System] Warte auf CONTINUE über M5Dial...")
    while True:
        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == CMD_CONTINUE:
                print("[System] CONTINUE erkannt.")
                return
        except:
            pass
        time.sleep(0.5)

def main():
    init_gpio()

    if is_notaus_active():
        print("[Init] NOT-AUS aktiv – warte auf CONTINUE")
        wait_for_continue()
    else:
        print("[Init] NOT-AUS nicht aktiv – sende CONTINUE an alle")
        send_command(ROBO_ADDR, CMD_CONTINUE, "Roboter")
        send_command(TURNTABLE_ADDR, CMD_CONTINUE, "Drehteller")

    print("[System] Starte Ablauf bei Startsignal vom M5Dial...")

    while True:
        try:
            status = bus.read_byte(M5DIAL_ADDR)
            if status == DIAL_START:
                print("[System] Startsignal erkannt – beginne Ablauf")

                for stueck in range(1, 11):
                    print(f"[System] Starte Bearbeitung für Stück {stueck}")

                    send_command(TURNTABLE_ADDR, TURN_MOVE_ASM, "Drehteller ASM")
                    wait_for_idle(TURNTABLE_ADDR, TURN_IDLE, "Drehteller ASM")

                    send_command(ROBO_ADDR, ROBO_MOVE_A, "Roboter MOVE_A")
                    wait_for_idle(ROBO_ADDR, ROBO_IDLE, "Roboter MOVE_A")

                    send_command(TURNTABLE_ADDR, TURN_MOVE_SND, "Drehteller SND")
                    wait_for_idle(TURNTABLE_ADDR, TURN_IDLE, "Drehteller SND")

                print("[System] Ablauf abgeschlossen.")

        except KeyboardInterrupt:
            print("[System] Beendet durch Nutzer.")
            break
        except Exception as e:
            print("[System] Fehler:", e)

        time.sleep(0.5)

    GPIO.cleanup()

main()
