import time
import sys
import RPi.GPIO as GPIO
import signal


pulse_pin = 37
direction_pin = 10
killswitch = 40
home_switch = 15

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pulse_pin, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin, GPIO.OUT)
GPIO.setup(killswitch, GPIO.IN)
GPIO.setup(home_switch, GPIO.IN)
global has_homed
global limit_reached

has_homed = False
limit_reached = False




def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def get_current():
    file = open("current_pos.txt", "r")
    past = int(file.read())
    return past

def overshoot(x):
    print('STOP: Detector has exceeded limit of operations')
    GPIO.output(pulse_pin, GPIO.LOW)
    print('stopped')
    global limit_reached
    limit_reached = True

def homing():
    GPIO.add_event_detect(home_switch, GPIO.FALLING, callback=homed, bouncetime = 100)
    print('Completing Homing')
    while has_homed == False:
        move_back_1(1)
    print('Done: The detector is now homed to 0mm')

def check_value(value, current):
    final_value = current + value
    if final_value < -100:
        result = False
    elif final_value > 10000:
        result = False
    else: 
        result = True
    return result

def homed(x):
    GPIO.output(pulse_pin, GPIO.LOW)
    print('Reached homing switch')
    save_value(0,'H')
    global has_homed
    has_homed = True
    
    

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

    

def move_forward_1(steps):
    GPIO.output(direction_pin, GPIO.LOW)
    
    if limit_reached == False:   
        x = 1
        while x<steps*320+1:
            GPIO.output(pulse_pin, GPIO.LOW)
            time.sleep(.001)
            GPIO.output(pulse_pin, GPIO.HIGH)
            time.sleep(.001)
            x = x+1
        GPIO.output(direction_pin, GPIO.HIGH)
        save_value(steps, 'F')
        
def move_back_1(steps):
    GPIO.output(direction_pin,GPIO.HIGH)
    
    if limit_reached == False:
        x = 1
        print('test')
        while x<320*steps+1:
            GPIO.output(pulse_pin, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(pulse_pin, GPIO.LOW)
            time.sleep(0.001)
            x = x+1
        save_value(steps, 'B')
        print('step')


GPIO.add_event_detect(killswitch, GPIO.FALLING, callback= overshoot, bouncetime=100)
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
            allowed = check_value(int(value), current)
            
            if allowed == True:
                move_forward_1(int(value))
                print('Moved forward:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'B':
            print('How much (0.1mm)')
            value = input()
            allowed = check_value(-int(value), current)
            if allowed == True:
                move_back_1(int(value))
                print('Moved forward:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'H':
            homing()
            print('Homed')
            continue
            
        else:
            print("Wrong value, try again")
            continue
        
        
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            break