import smbus2
import time

I2C_ADDR = 0x10  # I2C-Adresse des M5Dial
bus = smbus2.SMBus(1)  # I2C-Bus 1 für Raspberry Pi

print("Starte I2C-Überwachung von M5Dial (Adresse 0x10)")

try:
    while True:
        try:
            data = bus.read_byte(I2C_ADDR)
            print("→ Befehl vom M5Dial empfangen:", data)
        except OSError as e:
            if e.errno == 121:  # Remote I/O error = kein ACK (kein Gerät vorhanden)
                print("⚠ Kein Gerät antwortet auf Adresse 0x10")
            elif e.errno == 110:  # Timeout
                print("⚠ I2C Timeout – keine Antwort")
            else:
                print(f"❌ I2C-Fehler: {e}")
        time.sleep(0.2)  # 5x pro Sekunde prüfen

except KeyboardInterrupt:
    print("Beende I2C-Empfang.")
