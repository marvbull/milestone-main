import smbus
import time

# I2C-Adresse des Arduino
I2C_ADDR = 0x08
bus = smbus.SMBus(1)  # Bei Raspberry Pi ist Bus 1 üblich

def send_command(value):
    try:
        bus.write_byte(I2C_ADDR, value)
        print(f"→ Gesendet: {value}")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def request_status():
    try:
        status = bus.read_byte(I2C_ADDR)
        print(f"← Rohstatus vom Arduino: {status}")
        interpret_status(status)
    except Exception as e:
        print(f"Fehler beim Empfangen: {e}")

def interpret_status(status):
    if status == 1:
        print("🟢 Arduino bereit oder in Bewegung.")
    elif status == 10:
        print("✅ Move A abgeschlossen.")
    elif status == 20:
        print("✅ Move Test abgeschlossen.")
    elif status == 90:
        print("✅ Init abgeschlossen.")
    elif status == 99:
        print("⛔ NOTAUS erkannt.")
    else:
        print(f"⚠️ Unbekannter Statuscode: {status}")

def main():
    print("I2C-Steuerung bereit.")
    print("Befehle: a [1-10], init, test, stop, cont, status, exit")

    while True:
        cmd = input(">>> ").strip().lower()

        if cmd.startswith("a "):
            try:
                num = int(cmd.split()[1])
                if 1 <= num <= 10:
                    send_command(9 + num)  # 10–19 für moveA1–10
                else:
                    print("Nur Werte 1–10 erlaubt.")
            except ValueError:
                print("Ungültige Zahl.")
        elif cmd == "init":
            send_command(90)
        elif cmd == "test":
            send_command(20)
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

if __name__ == "__main__":
    main()
