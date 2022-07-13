import time
import sys
import RPi.GPIO as GPIO
import signal


pulse_pin = 37
direction_pin = 40
killswitch = test

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pulse_pin, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin, GPIO.OUT)


def get_current():
    file = open("current_pos.txt", "r")
    past = int(file.read())
    return past

def overshoot():
    if GPIO.input(killswitch):
        print('STOP: Detector has exceeded limit of operations')
        GPIO.output(pulse_pin, GPIO.LOW)

def homing():
    add_event_detect(killswitch, GPIO.FALLING, callback=homed)
    while True:
        move_back_1(1)


def homed():
    GPIO.output(pulse_pin, GPIO.LOW)
    save_value(0,'H')
    

def save_value(value, direction):
    file = open("current_pos.txt", "r")
    past = int(file.read())
    file.close()
    file = open("current_pos.txt", "w")
    if direction == 'F':
        current = past + int(value)
    elif direction == "B":
        current = past - int(value)
    elif direction == 'H':
        current = 0
    file.write(str(current))
    file.close()
    print("Postion is now:", current)
    

def move_forward_1(steps):
    GPIO.add_event_detect(killswitch, GPIO.FALLING, callback= overshoot)
    GPIO.output(direction_pin, GPIO.LOW)
    x = 1
    while x<steps*320+1:
        GPIO.output(pulse_pin, GPIO.LOW)
        time.sleep(.001)
        GPIO.output(pulse_pin, GPIO.HIGH)
        time.sleep(.001)
        x = x+1
    GPIO.output(direction_pin, GPIO.HIGH)
        
def move_back_1(steps):
    GPIO.add_event_detect(killswitch, GPIO.FALLING, callback= overshoot)
    GPIO.output(direction_pin,GPIO.HIGH)
    x = 1
    while x<320*steps+1:
        GPIO.output(pulse_pin, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(pulse_pin, GPIO.LOW)
        time.sleep(0.001)
        x = x+1
        
if __name__ =='__main__':
    while(True):
        current = get_current()
        print('===============================')
        print("Current value is:", current)
        print('Move Forward (F) or Back (B), or completing homing (H)')
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
        elif direction == 'H':
            homing()
            print('Homed')
        else:
            print("Wrong value, try again")
            continue
        save_value(value, direction)
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            break