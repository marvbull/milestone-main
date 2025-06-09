from smbus2 import SMBus
import time

I2C_ADDR = 0x09  # Arduino I2C-Adresse

# Befehle als Bytewerte
commands = {
    "moveasm": 30,
    "movesnd": 40,
    "movecal": 90,
    "movetest": 3,
    "stop": 99,
    "continue": 98
}

def send_command(bus, cmd_byte):
    try:
        bus.write_byte(I2C_ADDR, cmd_byte)
        print(f"Befehl {cmd_byte} gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def read_status(bus):
    try:
        response = bus.read_byte(I2C_ADDR)
        print(f"Empfangener Status vom Arduino: {response}")
    except Exception as e:
        print(f"Fehler beim Lesen: {e}")

def main():
    with SMBus(1) as bus:
        print("I2C-Terminal gestartet. Eingabe: moveasm / movesnd / movecal / movetest / stop / continue / status / exit")
        while True:
            user_input = input(">> ").strip().lower()
            if user_input == "exit":
                break
            elif user_input == "status":
                read_status(bus)
            elif user_input in commands:
                send_command(bus, commands[user_input])
            elif user_input.isdigit():
                send_command(bus, int(user_input))
            else:
                print("Ungültiger Befehl.")

if __name__ == "__main__":
    main()
