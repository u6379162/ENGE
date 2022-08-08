import time
import sys
import RPi.GPIO as GPIO
import signal
import csv

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
    data = []
    with open("current_pos.csv", newline='') as f:
        reader =csv.reader(f)
        data =list(reader)
    return data[0][0], data[0][1]


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
            move_1(-1,0)
            if GPIO.input(38)==0:
                count_A = count_A+1
                
        if count_B < 10:
            move_1(0,-1)
            if GPIO.input(37)==0:
                count_B = count_B+1
    print('Done: The detector rail is now homed to 0mm')
    
    


#Checks that the movement is allowed in the theoretical range:
def check_value(value_a, value_b, current_a, current_b):
    final_value_a = float(current_a) + float(value_a)
    final_value_b = float(current_b) + float(value_b)    
    if final_value_a < -100:
        result = False
    elif final_value_a > 3000:
        result = False
    elif final_value_b < -100:
        result = False
    elif final_value_b > 3000:
        result = False
    else: 
        result = True
    return result


#Saves the moved value to the file for future use:
def save_value(value_a, value_b):
    current_a, current_b = get_current()
    new = (float(current_a) + float(value_a), float(current_b) + float(value_b))
    f = open('current_pos.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(new)
    f.close()




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
def move_1(steps_A, steps_B):
                                                                #Set the directional input to the driver
    if steps_A > 0:
        GPIO.output(direction_pin_A, GPIO.LOW)
       
    elif steps_A < 1:
        GPIO.output(direction_pin_A, GPIO.HIGH)
        
    if steps_A > 0:
        GPIO.output(direction_pin_B, GPIO.LOW)
        
    elif steps_B < 1:
        GPIO.output(direction_pin_B, GPIO.HIGH)


    if limit_reached == False:        #stops if a limit switch is actiavted
        x_A = 1
        x_B = 1
        x = 1
        max_steps = max(abs(steps_A), abs(steps_B))
        
        while x<max_steps*320+1:       #keeps looping until the biggest movement is complete
            
            if x_A < abs(steps_A)*320+1:                   #320 is the number of pulses required to move 1mm 
                GPIO.output(pulse_pin_A, GPIO.LOW)
                time.sleep(speed)
                GPIO.output(pulse_pin_A, GPIO.HIGH)
                time.sleep(speed)
                x_A = x_A +1
                
            if x_B < abs(steps_B)*320+1:
                GPIO.output(pulse_pin_B, GPIO.LOW)
                time.sleep(speed)
                GPIO.output(pulse_pin_B, GPIO.HIGH)
                time.sleep(speed)
                x_B = x_B +1

            if limit_reached == True:       #handles the limit switch being activated
                x = max_steps*320+1
                print('true')
            x = x+1
            
        save_value(steps_A, steps_B )
        


if __name__ =='__main__':
    #GPIO.add_event_detect(killswitch_A_1, GPIO.FALLING, callback= overshoot,bouncetime=1)
    while(True):
        print(GPIO.input(38))
#         time.sleep(0.1)
        current_a, current_b = get_current()

        print('===============================')
        print("Current value for A is:", current_a, '        Current value for B is :', current_b)
        print('Move same (S), completing homing (H)  or Dual (D)')
        print('===============================')
        
        routine = input()

        
        if routine == 'S':
            print('How much (0.1mm), postive is forward, negative is backwards')
            value = input()
            allowed = check_value(float(value), float(value), current_a, current_b)
            
            if allowed == True:
                move_1(float(value), float(value))
                print('Moved:', value)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
        
        elif routine == 'H':
            homing()
            current_a, current_b = get_current()
            print('Homed')
            save_value(-float(current_a),-float(current_b))
            continue
            
        elif routine == 'D':
            motorA_dist = input('Motor A distance:')
            motorB_dist = input('Motor B distance:')
            allowed = check_value(float(motorA_dist), float(motorB_dist), current_a, current_b)
            if allowed == True:
                move_1(float(motorA_dist), float(motorB_dist))
                print('Moved A:', motorA_dist, '   Moved B:', motorB_dist)
            elif allowed == False:
                print("Operation not allowed: will breach limit of movement")
            
        else:
            print("Wrong value, try again")
            continue
        
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            GPIO.cleanup()
            break