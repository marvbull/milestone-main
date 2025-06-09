# I2C-Adressen
M5DIAL_ADDR = 0x10
TURNTABLE_ADDR = 0x09
ROBO_ADDR = 0x08

# Befehle (Base ist immer + Stückzahl)
DIAL_IDLE = 0 # Idle-Status
DIAL_START = 1 # Start des Produktionsprozesses
DIAL_STOP = 2 # Stop des Produktionsprozesses
DIAL_QUIT = 3 # Quitieren des Programmes

ROBO_MOVE_A = 10 # Montage des Bandes
ROBO_MOVE_TEST = 20 # Ausgabe des ASM
TURN_MOVE_ASM = 30 # Platten aufeinanderstacken
TURN_MOVE_SND = 40 # Solanoid auf

CMD_CALIBRATE = 90 # init
CMD_CONTINUE = 98 # Weiter über I2C
CMD_STOP = 99 # Stoo über I2C

# Rückmeldungen
RESP_DONE_ROBO_A = 10
RESP_DONE_ROBO_B = 20
RESP_DONE_TURN_ASM = 30
RESP_DONE_TURN_SND = 40
RESP_DONE_CALIBRATE = 90


RESP_ERROR = 255