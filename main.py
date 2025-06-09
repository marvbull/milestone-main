import smbus
import time

bus = smbus.SMBus(1)
ADDR_TURNTABLE = 0x07
ADDR_ROBOT = 0x08

def warte_weiter():
    while True:
        cmd = input("Eingabe 'weiter' zum Fortfahren: ").strip().lower()
        if cmd == "weiter":
            return

def main():
    print("Starte manuellen Ablauf. Reihenfolge: 30 → 10 → 40")

    warte_weiter()
    print("[1] Drehteller → 30")
    bus.write_byte(ADDR_TURNTABLE, 30)

    warte_weiter()
    print("[2] Roboter → 10")
    bus.write_byte(ADDR_ROBOT, 10)

    warte_weiter()
    print("[3] Drehteller → 40")
    bus.write_byte(ADDR_TURNTABLE, 40)

    print("Ablauf abgeschlossen.")

if __name__ == "__main__":
    main()
