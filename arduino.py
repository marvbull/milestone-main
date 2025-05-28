import i2c
import time

def moveRobo(addr, befehl):
    i2c.write_byte(addr, befehl)
    
    while True:
        status = i2c.read_byte(addr)
        if status is None:
            time.sleep(0.2)
            continue

        if status in [10, 20]:
            return status
        time.sleep(0.2)
