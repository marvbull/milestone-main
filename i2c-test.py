import smbus
import time

I2C_ADDR = 0x08  # Adresse des Arduino
bus = smbus.SMBus(1)  # SMBus 1 für Raspberry Pi

def send_command(cmd):
    try:
        print(f"Sende I2C-Befehl: {cmd}")
        bus.write_byte(I2C_ADDR, cmd)
        time.sleep(0.1)
        response = bus.read_byte(I2C_ADDR)
        print(f"Antwort vom Arduino: {response}")
    except Exception as e:
        print(f"Fehler bei I2C: {e}")

def main():
    print("Gib eine Zahl von 10–19 ein (Band 1–10).")
    print("Oder andere bekannte Kommandos wie 2 (moveB), 30 (moveTest).")

    while True:
        try:
            raw_input = input("Befehl senden (q zum Beenden): ").strip()
            if raw_input.lower() == "q":
                break
            cmd = int(raw_input)
            send_command(cmd)
        except ValueError:
            print("Ungültige Eingabe. Bitte eine Zahl eingeben.")
        except KeyboardInterrupt:
            print("\nBeendet.")
            break

if __name__ == "__main__":
    main()
