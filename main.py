import i2c
from arduino import moveRobo

ROBO_ADDR = 0x08

def main():
    i2c.init_i2c()
    
    print("Starte Bewegung A...")
    status = moveRobo(ROBO_ADDR, 1)  # 1 = Move A
    
    if status == 10:
        print("Bewegung A abgeschlossen.")
    else:
        print(f"Unbekannter Statuscode: {status}")
    
    i2c.close_i2c()

if __name__ == "__main__":
    main()
