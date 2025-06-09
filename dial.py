import smbus
import time

I2C_ADDR = 0x10  # Adresse des Arduino-Slave

bus = smbus.SMBus(1)  # I2C-1 beim Raspberry Pi

# Sende ein Byte
bus.write_byte(I2C_ADDR, 4)
time.sleep(0.1)

# Lese bis zu 6 Zeichen vom Arduino
response = bus.read_byte(I2C_ADDR)
print("Antwort vom Arduino:", response)
