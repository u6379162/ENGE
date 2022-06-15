import time
import sys
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(37, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(40, GPIO.OUT)

def get_current():
    file = open("current_pos.txt", "r")
    past = int(file.read())
    return past
    

def save_value(value, direction):
    file = open("current_pos.txt", "r")
    past = int(file.read())
    file.close()
    file = open("current_pos.txt", "w")
    if direction == 'F':
        current = past + int(value)
    elif direction == "B":
        current = past - int(value)
    file.write(str(current))
    file.close()
    print("Postion is now:", current)
    

def move_forward_1(steps):
    GPIO.output(40, GPIO.LOW)
    x = 1
    while x<steps*320+1:
        GPIO.output(37, GPIO.LOW)
        time.sleep(.001)
        GPIO.output(37, GPIO.HIGH)
        time.sleep(.001)
        x = x+1
    GPIO.output(40, GPIO.HIGH)
        
def move_back_1(steps):
    GPIO.output(40,GPIO.HIGH)
    x = 1
    while x<320*steps+1:
        GPIO.output(37, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(37, GPIO.LOW)
        time.sleep(0.001)
        x = x+1
        
if __name__ =='__main__':
    while(True):
        current = get_current()
        print('===============================')
        print("Current value is:", current)
        print('Move Forward (F) or Back (B)')
        print('===============================')
        direction = input()
        if direction == 'F':
            print('How much (0.1mm)')
            value = input()
            move_forward_1(int(value))
            print('Moved forward:', value)
        elif direction == 'B':
            print('How much (0.1mm)')
            value = input()
            move_back_1(int(value))
            print('Moved back', value)
        else:
            print("Wrong value, try again")
            continue
        save_value(value, direction)
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            break