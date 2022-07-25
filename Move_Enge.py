import time
import sys
import RPi.GPIO as GPIO
import signal

# Setting up all of the pin outs

#pulse and direction are used to control the stepper motor driver:
pulse_pin_A = 11
direction_pin_A = 13
pulse_pin_B = 16
direction_pin_B = 18

#Kill switchs are the limit switchs to kill movement:
killswitch_A_1 = 29
killswitch_A_2 = 31
killswitch_B_1 = 33
killswitch_B_2 = 35

#Home switch A and B is for each rail to hom to, should be the referance 0mm:
home_switch_A = 37
home_switch_B = 36

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pulse_pin_A, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin_A, GPIO.OUT)
GPIO.setup(pulse_pin_B, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin_B, GPIO.OUT)
GPIO.setup(killswitch_A_1, GPIO.IN)
GPIO.setup(killswitch_A_2, GPIO.IN)
GPIO.setup(killswitch_B_1, GPIO.IN)
GPIO.setup(killswitch_B_2, GPIO.IN)
GPIO.setup(home_switch_A, GPIO.IN)
GPIO.setup(home_switch_B, GPIO.IN)

#Setting global variables to use for interupts
global has_homed_A
global has_homed_B
global limit_reached

has_homed_A = False
has_homed_B = False
limit_reached = False




def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)


#Get the current postion of the detector from the file:
def get_current():
    file = open("current_pos.txt", "r")
    past = int(file.read())
    return past


#Interupt if a limit switch is activated:
def overshoot(x):
    print('STOP: Detector has exceeded limit of operations')
    GPIO.output(pulse_pin, GPIO.LOW)
    limit_reached = True
    print('Oh NO')
    

#Homing procedure for the A rail
def homing_A():
    GPIO.add_event_detect(home_switch_A, GPIO.FALLING, callback=homed_A, bouncetime = 10)
    print('Completing Homing of A')
    while has_homed_A == False:
        move_back_1(1,0)
    print('Done: The detector A rail is now homed to 0mm')
    
    
#Homing procedure for rail B    
def homing_B():
    GPIO.add_event_detect(home_switch_B, GPIO.FALLING, callback=homed_B, bouncetime = 10)
    print('Completing Homing of B')
    while has_homed_B == False:
        move_back_1(0,1)
    print('Done: The detector B rail is now homed to 0mm') 


#Checks that the movement is allowed in the theoretical range:
def check_value(value, current):
    final_value = current + value
    if final_value < -100:
        result = False
    elif final_value > 5000:
        result = False
    else: 
        result = True
    return result


#Interupts when the A rail has homed:
def homed_A(x):
    GPIO.output(pulse_pin_A, GPIO.LOW)
    print('Reached homing switch A')
    save_value(0,'H')
    has_homed_A = True
    
    
#Interupts when the B rail has homed:
def homed_B(x):
    GPIO.output(pulse_pin_B, GPIO.LOW)
    print('Reached homing switch A')
    save_value(0,'H')
    has_homed_B = True
    

#Saves the moved value to the file for future use:
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

    
# Used to move the rail forward 1mm:
def move_forward_1(steps_A, steps_B):
    
    GPIO.output(direction_pin_A, GPIO.LOW)    #Set the directional input to the driver
    GPIO.output(direction_pin_B, GPIO.LOW)

    if limit_reached == False:        #stops if a limit switch is actiavted
        x_A = 1
        x_B = 1
        x = 1
        max_steps = max(steps_A, steps_B)
        
        while x<max_steps*320+1:       #keeps looping until the biggest movement is complete
            
            if x_A < steps_A*320+1:                   #320 is the number of pulses required to move 1mm 
                GPIO.output(pulse_pin_A, GPIO.LOW)
                time.sleep(.00001)
                GPIO.output(pulse_pin_A, GPIO.HIGH)
                time.sleep(.00001)
                x_A = x_A +1
                
            if x_B < steps_B*320+1:
                GPIO.output(pulse_pin_B, GPIO.LOW)
                time.sleep(.00001)
                GPIO.output(pulse_pin_B, GPIO.HIGH)
                time.sleep(.00001)
                x_B = x_B +1

            if limit_reached == True:       #handles the limit switch being activated
                x = max_steps*320+1
                print('true')
            x = x+1
        save_value(max_steps, 'F')
        
def move_back_1(steps_A, steps_B):
    GPIO.output(direction_pin_A, GPIO.HIGH)
    GPIO.output(direction_pin_B, GPIO.HIGH)
    
    if limit_reached == False:   
        x_A = 1
        x_B = 1
        x = 1
        max_steps = max(steps_A, steps_B)
        
        while x<max_steps*320+1:
            if x_A < steps_A*320+1:
                GPIO.output(pulse_pin_A, GPIO.LOW)
                time.sleep(.00001)
                GPIO.output(pulse_pin_A, GPIO.HIGH)
                time.sleep(.00001)
                x_A = x_A +1
                
            if x_B < steps_B*320+1:
                GPIO.output(pulse_pin_B, GPIO.LOW)
                time.sleep(.00001)
                GPIO.output(pulse_pin_B, GPIO.HIGH)
                time.sleep(.00001)
                x_B = x_B +1

            if limit_reached == True:
                x = max_steps*320+1
                print('true')
            x = x+1
        save_value(max_steps, 'B')


if __name__ =='__main__':
    GPIO.add_event_detect(killswitch_A_1, GPIO.FALLING, callback= overshoot)
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
                move_forward_1(int(value), int(value))
                print('Moved forward:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'B':
            print('How much (0.1mm)')
            value = input()
            allowed = check_value(-int(value), current)
            if allowed == True:
                move_back_1(int(value), int(value))
                print('Moved forward:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'H':
            homing_A()
            homing_B()
            print('Homed')
            continue
            
        else:
            print("Wrong value, try again")
            continue
        
        
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            GPIO.cleanup()
            break