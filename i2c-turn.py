import smbus
import time

I2C_ADDR = 0x09  # I2C-Adresse des Arduino
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
                time.sleep(0.5)
                request_status()
            else:
                print("! Wert außerhalb [0–255]")
        except ValueError:
            print("! Ungültige Eingabe")

if __name__ == "__main__":
    main()
