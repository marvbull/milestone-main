from i2c import bus
import time
import constants

def moveRobo(addr, befehl):
    try:
        print(f"Sende Befehl {befehl}")
        bus.write_byte(addr, befehl)

        # Antwort vom Arduino (z. B. wenn Bewegung fertig)
        rueck = bus.read_byte(addr)
        print(f"Antwort {rueck}")
        return rueck
    except Exception as e:
        print("I2C-Fehler:", e)
        return None