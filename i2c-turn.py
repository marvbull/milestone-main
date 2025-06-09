import smbus
import time

I2C_ADDR = 0x09  # I2C-Adresse des Arduino
bus = smbus.SMBus(1)  # I2C-Bus des Raspberry Pi

def send_command(value):
    try:
        bus.write_byte(I2C_ADDR, value)
        print(f"→ Befehl gesendet: {value}")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def request_status():
    try:
        status = bus.read_byte(I2C_ADDR)
        print(f"← Status vom Arduino: {status}")
        return status
    except Exception as e:
        print(f"Fehler beim Empfangen: {e}")
        return -1

def main():
    print("I²C-Steuerung bereit.")
    print("Befehle: cal, asm, snd, stop, cont, status, exit")

    while True:
        cmd = input(">>> ").strip().lower()

        if cmd == "cal":
            send_command(90)
        elif cmd == "asm":
            send_command(30)
        elif cmd == "snd":
            send_command(40)
        elif cmd == "stop":
            send_command(99)
        elif cmd == "cont":
            send_command(98)
        elif cmd == "status":
            request_status()
        elif cmd == "exit":
            break
        else:
            print("Unbekannter Befehl.")

        # Automatisch Rückmeldung abfragen
        time.sleep(0.5)
        request_status()

if __name__ == "__main__":
    main()
