import smbus
import time

bus = smbus.SMBus(1)

ADDR_M5DIAL = 0x10
ADDR_ARDUINO1 = 0x09
ADDR_ARDUINO2 = 0x08

def read_byte(addr):
    try:
        val = bus.read_byte(addr)
        print(f"← {addr:#04x} {val}")
        return val
    except Exception as e:
        print(f"! {addr:#04x} {e}")
        return -1

def write_byte(addr, val):
    try:
        bus.write_byte(addr, val)
        print(f"→ {addr:#04x} {val}")
    except Exception as e:
        print(f"! {addr:#04x} {e}")

def wait_for_status(addr, expected_val, delay=2):
    while True:
        time.sleep(delay)
        status = read_byte(addr)
        if status == expected_val:
            break

def main():
    print("Warte auf Startsignal (1) von M5Dial...")

    # 1. Warten auf Start von M5Dial
    while True:
        val = read_byte(ADDR_M5DIAL)
        if val == 1:
            print("Startsignal empfangen.")
            break
        time.sleep(1)

    # 2. Senden 30 an Arduino1 (0x09) und auf 125 warten
    write_byte(ADDR_ARDUINO1, 30)
    wait_for_status(ADDR_ARDUINO1, 125)

    # 3. Senden 10 an Arduino2 (0x08) und auf 105 warten
    write_byte(ADDR_ARDUINO2, 10)
    wait_for_status(ADDR_ARDUINO2, 105)

    # 4. Senden 40 an Arduino1 (0x09) und auf 125 warten
    write_byte(ADDR_ARDUINO1, 40)
    wait_for_status(ADDR_ARDUINO1, 125)

    # 5. Eingabe: weiter oder exit
    while True:
        cmd = input(">>> ").strip().lower()
        if cmd == "exit":
            break
        elif cmd == "weiter":
            print("Warte auf neues Startsignal...")
            main()  # Neustart des Ablaufs
            break
        else:
            print("Nur 'weiter' oder 'exit' erlaubt.")

if __name__ == "__main__":
    main()
