#Datei: i2c_master.py
from smbus2 import SMBus
import time

ARDUINO_ADDR = 0x08  # I2C-Adresse des Arduino

with SMBus(1) as bus:
    while True:
        try:
            value_to_send = 42
            print(f"Sende an Arduino: {value_to_send}")
            bus.write_byte(ARDUINO_ADDR, value_to_send)
            time.sleep(0.1)  # Warte auf Antwort
            response = bus.read_byte(ARDUINO_ADDR)
            print(f"Antwort vom Arduino: {response}")
        except Exception as e:
            print("Fehler:", e)
        time.sleep(1)