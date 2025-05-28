from i2c import bus
import time

COMMANDS = {
    1: "Roboter: move A",
    2: "Roboter: move B",
    10: "Drehteller: nach links drehen",
    11: "Drehteller: nach rechts drehen",
    20: "Roboter: kalibrieren",
    99: "System: STOP"
}

RECEIVE = {
    10: "Roboter: Bewegung A abgeschlossen",
    11: "Roboter: Bewegung B abgeschlossen",
    20: "Drehteller: Drehung abgeschlossen",
    255: "Fehler"
}

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