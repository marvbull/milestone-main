# Datei: i2c.py
import time
from smbus2 import SMBus

bus = None

def init_i2c(bus_number=1):
    global bus
    try:
        bus = SMBus(bus_number)
        print("I2C-Bus initialisiert.")
    except Exception as e:
        print("Fehler beim Initialisieren des I2C-Bus:", e)
        bus = None

def write_byte(addr, value):
    global bus
    if bus is None:
        print("⚠️ Fehler: I2C-Bus wurde nicht initialisiert!")
        return
    try:
        bus.write_byte(addr, value)
    except Exception as e:
        print(f"I2C Write Error @ 0x{addr:02X}: {e}")

def read_byte(addr):
    global bus
    if bus is None:
        print("⚠️ Fehler: I2C-Bus wurde nicht initialisiert!")
        return None
    try:
        return bus.read_byte(addr)
    except Exception as e:
        print(f"I2C Read Error @ 0x{addr:02X}: {e}")
        return None

def close_i2c():
    global bus
    if bus:
        bus.close()
        bus = None

#import i2c
#i2c.init_i2c()
#i2c.write_byte(0x08, 42)
#value = i2c.read_byte(0x08)