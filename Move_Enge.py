import time
import sys
import RPi.GPIO as GPIO
import signal

# Setting up all of the pin outs

#pulse and direction are used to control the stepper motor driver:
pulse_pin_A = 11
direction_pin_A = 13
pulse_pin_B = 18
direction_pin_B = 16

output_pin = 40

#Kill switchs are the limit switchs to kill movement:
killswitch_A_1 = 29
killswitch_A_2 = 31
killswitch_B_1 = 33
killswitch_B_2 = 35

#Home switch A and B is for each rail to hom to, should be the referance 0mm:
home_switch_A = 37
home_switch_B = 38


GPIO.setmode(GPIO.BOARD)

GPIO.setwarnings(False)
GPIO.setup(output_pin, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(pulse_pin_A, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin_A, GPIO.OUT)
GPIO.setup(pulse_pin_B, GPIO.OUT, initial= GPIO.HIGH)
GPIO.setup(direction_pin_B, GPIO.OUT)
GPIO.setup(killswitch_A_1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(killswitch_A_2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(killswitch_B_1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(home_switch_B, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(killswitch_B_2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(home_switch_A, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)


speed = 0.0000001

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
    past = float(file.read())

    return past


#Interupt if a limit switch is activated:
def overshoot(x):
    #print('STOP: Detector has exceeded limit of operations')
    GPIO.output(pulse_pin_A, GPIO.LOW)
    global limit_reached
    limit_reached = True
    #print('Oh NO')
    

#Homing procedure 
def homing():
    print('Completing Homing')
    count_A =0
    count_B = 0
    while min(count_A, count_B)< 10:
        
        if count_A < 10:
            move_1(1,0,'B','B')
            if GPIO.input(38)==0:
                count_A = count_A+1
                
        if count_B < 10:
            move_1(0,1,'B','B')
            if GPIO.input(37)==0:
                count_B = count_B+1
    print('Done: The detector rail is now homed to 0mm')
    
    


#Checks that the movement is allowed in the theoretical range:
def check_value(value, current):
    final_value = current + value
    if final_value < -10000:
        result = False
    elif final_value > 5000:
        result = False
    else: 
        result = True
    return result


#Saves the moved value to the file for future use:
def save_value(value, direction):
    file = open("current_pos.txt", "r")
    past = file.read()
    file.close()
    file = open("current_pos.txt", "w")
    if direction == 'F':
        current = float(past) + float(value)
    elif direction == "B":
        current = float(past) - float(value)
    elif direction == 'H':
        current = 0
    file.write(str(current))
    file.close()




def required_movement(current_A, current_B, k_value):
    reqiured_pos_A = k*Xa + Ya
    reqiured_pos_B = k*Xb + Yb
    
    move_A = required_pos_A - current_A
    move_B = required_pos_B - current_B
    
    if move_A > 0:
        dir_A = 'F'
    else: dir_A = 'B'

    if move_B > 0:
        dir_B = 'F'
    else: dir_B = 'B'

    return (dir_A, abs(move_A), dir_B, abs(move_B))
    
    
    
# Used to move the rail forward 1mm:
def move_1(steps_A, steps_B, direction_A1, direction_B1):

                                                                #Set the directional input to the driver
    if direction_A1 == 'F':
        GPIO.output(direction_pin_A, GPIO.LOW)
       
    elif direction_A1 == 'B':
        GPIO.output(direction_pin_A, GPIO.HIGH)
        
    if direction_B1 == 'F':
        GPIO.output(direction_pin_B, GPIO.LOW)
        
    elif direction_B1 == 'B':
        GPIO.output(direction_pin_B, GPIO.HIGH)


    if limit_reached == False:        #stops if a limit switch is actiavted
        x_A = 1
        x_B = 1
        x = 1
        max_steps = max(steps_A, steps_B)
        
        while x<max_steps*320+1:       #keeps looping until the biggest movement is complete
            
            if x_A < steps_A*320+1:                   #320 is the number of pulses required to move 1mm 
                GPIO.output(pulse_pin_A, GPIO.LOW)
                time.sleep(speed)
                GPIO.output(pulse_pin_A, GPIO.HIGH)
                time.sleep(speed)
                x_A = x_A +1
                
            if x_B < steps_B*320+1:
                GPIO.output(pulse_pin_B, GPIO.LOW)
                time.sleep(speed)
                GPIO.output(pulse_pin_B, GPIO.HIGH)
                time.sleep(speed)
                x_B = x_B +1

            if limit_reached == True:       #handles the limit switch being activated
                x = max_steps*320+1
                print('true')
            x = x+1
            
        save_value(max_steps, 'F')
        


if __name__ =='__main__':
    #GPIO.add_event_detect(killswitch_A_1, GPIO.FALLING, callback= overshoot,bouncetime=1)
    while(True):
        print(GPIO.input(38))
#         time.sleep(0.1)
        current = get_current()

        print('===============================')
        print("Current value is:", current)
        print('Move Forward (F) or Back (B), or completing homing (H)  or Dual (D)')
        print('===============================')
    
       
        
        direction = input()

        
        if direction == 'F':
            print('How much (0.1mm)')
            value = input()
            allowed = check_value(float(value), current)
            
            if allowed == True:
                move_1(float(value), float(value),'F','F')
                print('Moved forward:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'B':
            print('How much (0.1mm)')
            value = input()
            allowed = check_value(-float(value), current)
            if allowed == True:
                move_1(float(value), float(value), 'B', 'B')
                print('Moved back:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif direction == 'H':
            homing()
            print('Homed')
            save_value(0,'H')
            continue
            
        elif direction == 'D':
            motorA_dir = input('Motor A direction:')
            motorA_dist = input('Motor A distance:')
            motorB_dir = input('Motor B direction:')
            motorB_dist = input('Motor B distance:')
            move_1(float(motorA_dist), float(motorB_dist), motorA_dir, motorB_dir)
            
        else:
            print("Wrong value, try again")
            continue
        
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            GPIO.cleanup()
            break