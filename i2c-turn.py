import smbus
import time

I2C_ADDR = 0x09
bus = smbus.SMBus(1)

def send_command(value):
    try:
        bus.write_byte(I2C_ADDR, value)
        print(f"→ {value}")
    except Exception as e:
        print(f"! {e}")

def request_status():
    try:
        status = bus.read_byte(I2C_ADDR)
        print(f"← {status}")
        return status
    except Exception as e:
        print(f"! {e}")
        return -1

def main():
    while True:
        try:
            value = input(">>> ").strip()
            if value == "exit":
                break
            byte_value = int(value)
            if 0 <= byte_value <= 255:
                send_command(byte_value)
                
                # Status alle 2 Sekunden abfragen, bis 125 zurückkommt
                while True:
                    time.sleep(2)
                    status = request_status()
                    if status == 125:
                        break
            else:
                print("! Wert außerhalb [0–255]")
        except ValueError:
            print("! Ungültige Eingabe")

if __name__ == "__main__":
    main()
