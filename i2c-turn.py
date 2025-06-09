import smbus
import time

# I2C-Adresse des Arduino (laut Wire.begin(0x09))
I2C_ADDR = 0x09
bus = smbus.SMBus(1)  # Bus 1 ist Standard auf dem Raspberry Pi

def send_command(value):
    try:
        bus.write_byte(I2C_ADDR, value)
        print(f"→ Gesendet: {value}")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def request_status():
    try:
        status = bus.read_byte(I2C_ADDR)
        print(f"← Status vom Arduino: {status}")
    except Exception as e:
        print(f"Fehler beim Empfangen: {e}")

def main():
    print("I2C-Terminal für Arduino (Adresse 0x09)")
    print("Befehle: a [1-10], init, test, snd, stop, cont, status, exit")

    while True:
        cmd = input(">>> ").strip().lower()

        if cmd.startswith("a "):
            try:
                num = int(cmd.split()[1])
                if 1 <= num <= 10:
                    send_command(9 + num)  # 10 bis 19
                else:
                    print("Nur Werte 1–10 erlaubt.")
            except ValueError:
                print("Ungültige Eingabe.")
        elif cmd == "init":
            send_command(90)  # moveCAL
        elif cmd == "test":
            send_command(30)  # moveASM
        elif cmd == "snd":
            send_command(40)  # moveSND
        elif cmd == "stop":
            send_command(99)
        elif cmd == "cont":
            send_command(98)
        elif cmd == "status":
            request_status()
        elif cmd == "exit":
            print("Beendet.")
            break
        else:
            print("Unbekannter Befehl. Verwende: a [1-10], init, test, snd, stop, cont, status, exit")

if __name__ == "__main__":
    main()
