from i2c import bus
import time
import constants

def moveRobo(addr, befehl):
    try:
        print(f"Sende Befehl {befehl} an Adresse {hex(addr)}")
        bus.write_byte(addr, befehl)
        time.sleep(0.05)  # kurze Wartezeit, damit Arduino reagieren kann

        # Versuche mehrfach, eine gültige Rückmeldung zu bekommen
        for i in range(10):
            try:
                rueck = bus.read_byte(addr)
                print(f"Antwort von {hex(addr)}: {rueck}")
                return rueck
            except Exception as e_inner:
                print(f"Versuch {i+1}/10 – keine Antwort, warte...")
                time.sleep(0.2)

        print(f"Keine Antwort von {hex(addr)} nach 10 Versuchen.")
        return None

    except Exception as e:
        print(f"I2C-Fehler bei Adresse {hex(addr)}:", e)
        return None
