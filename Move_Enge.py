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
killswitch_A_1 = 32
killswitch_A_2 = 31
killswitch_B_1 = 33
killswitch_B_2 = 35

#Home switch A and B is for each rail to hom to, should be the referance 0mm:
home_switch_A = 38
home_switch_B = 37

#Set up intial conditions of the GPIO pins
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


speed = 0.00001

#Setting global variables to use for interupts
global limit_reached
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


#Function used to move the mount points to load and unload the detector    
def load():
    confirm = input('Has the detctor been lowered? (Y/N)')      #Mount point requires lowering before the rail can be loaded.
    if confirm =='Y':
        A_current, B_current = get_current()
        move_1(3350-float(A_current), -float(B_current)-650, .0000001)
    else: print('========================\n Lower detector before proceeding \n ======================') 
    

#Homing procedure to move detector to reference position 0,0
def homing():
    print('Completing Homing')
    count_A =0
    count_B = 0
    A_back_count =0
    B_back_count =0

    while min(A_back_count, B_back_count)< 19:
        if A_back_count < 20:
            move_1(1,0, 0.000001)
            if GPIO.input(38)==1:
                A_back_count = A_back_count+1
            if GPIO.input(38)==0:
                A_back_count = 0
        if B_back_count < 20:
            move_1(0,1, 0.000001)
            if GPIO.input(37)==1:
                B_back_count = B_back_count+1
            if GPIO.input(37)==0:
                B_back_count = 0
        
    while min(count_A, count_B)< 19:
        if count_A < 20:
            move_1(-1,0, 0.000001)
            if GPIO.input(38)==0:
                count_A = count_A+1
            if GPIO.input(38)==1:
                count_A = 0
        if count_B < 20:
            move_1(0,-1, 0.000001)
            if GPIO.input(37)==0:
                count_B = count_B+1
            if GPIO.input(37)==1:
                count_B = 0
    print('Done: The detector rail is now homed to 0mm')
    
    


#Checks that the movement is allowed in the theoretical range, and the angle of movement is allowed:
def check_value(value_a, value_b, current_a, current_b):
    final_value_a = float(current_a) + float(value_a)
    final_value_b = float(current_b) + float(value_b)    
    if final_value_a < -600:
        result = False
    elif final_value_a > 3350:
        result = False
    elif final_value_b < -600:
        result = False
    elif final_value_b > 3350:
        result = False
        
    elif abs(final_value_a - final_value_b) > 500:
        if final_value_a >3000:
            if final_value_b < 3000:
                result = False
            else: result = True
            
        if final_value_b >3000:
            if final_value_a < 3000:
                result = False
            else: result = True
            
        if final_value_a <-300:
            if final_value_b > -600:
                result = False
            else: result = True
            
        if final_value_b <-300:
            if final_value_a > -600:
                result = False
            else: result = True
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


#Determines the required movement of the detector based on the K value given to it.
def required_move(current_A, current_B, k_value):
    required_pos_A = 600 #k_value*Xa + Ya    <---- Input data here once calibrated
    required_pos_B = 600 #k_value*Xb + Yb
    
    move_A = float(required_pos_A) - float(current_A)
    move_B = float(required_pos_B) - float(current_B)
    print(move_A, move_B)
    return (move_A, move_B)
    
    
    
# Used to move the rail forward 1mm:
def move_1(steps_A, steps_B, speed = 0.00001):

    #Set the directional input to the driver
    if steps_A > 0:
        GPIO.output(direction_pin_A, GPIO.LOW)
       
    elif steps_A < 1:
        GPIO.output(direction_pin_A, GPIO.HIGH)
        
    if steps_B > 0:
        GPIO.output(direction_pin_B, GPIO.LOW)
        
    elif steps_B < 1:
        GPIO.output(direction_pin_B, GPIO.HIGH)
   
    limit_reached = False

    if limit_reached == False:        #stops if a limit switch is actiavted
        x_A = 1
        x_B = 1
        x = 1
        max_steps = max(abs(steps_A), abs(steps_B))
        
        while x<max_steps*320+1:       #keeps looping until the biggest movement is complete
            
            #Checks that limit switches have not been activated 10 times 
            trigger = GPIO.input(killswitch_A_1) * GPIO.input(killswitch_A_2) *  GPIO.input(killswitch_B_1) * GPIO.input(killswitch_B_2) 
            if trigger == 0:
                limit_test = 0
                tripped = 0
                while limit_test < 10:
                    trigger = GPIO.input(killswitch_A_1) * GPIO.input(killswitch_A_2) *  GPIO.input(killswitch_B_1) * GPIO.input(killswitch_B_2) 
                    if trigger == 0:
                        tripped = tripped+1
                    time.sleep(0.00001)
                    limit_test = limit_test +1

                # If the limit switches are triggered in 7 out of the 10 times, it will stop the movement
                if tripped > 7:
                    print('STOP: The detector is at the limit of operation')
                    limit_reached = True
                    


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
                dont_save = 1

            x = x+1
        if dont_save == 1:
            print('Re-home or open up Enge')
        else:
            save_value(steps_A, steps_B)
            print('Moved A:', steps_A, '   Moved B:', steps_B)
        
# Takes the K value given and moves to the correct position
def experimental():
    k_value = input('Kinematic broadening value k:')
    current_a, current_b = get_current()
    a, b = required_move(current_a, current_b, k_value)
    if check_value(a, b, current_a, current_b) = True:
        print(a,b)
        move_1(a, b)
        print('Move completed')
    
        
  # Manual overide to use for calibration and other needs      
def manual():
    motorA_dist = input('Motor A distance:')
    motorB_dist = input('Motor B distance:')
    allowed = check_value(float(motorA_dist), float(motorB_dist), current_a, current_b)
    if allowed == True:
        move_1(float(motorA_dist), float(motorB_dist))
    elif allowed == False:
        print("Operation not allowed: will breach limit of movement")
    

if __name__ =='__main__':
    
    while(True):
        current_a, current_b = get_current()

        print('===============================')
        print("Current value for A is:", current_a, '        Current value for B is :', current_b)
        print('Manual(M), Homing (H), Load (L) or Experimental(E))')
        print('===============================')
        
        routine = input()

        
        if routine == 'H':
            homing()
            current_a, current_b = get_current()
            save_value(-float(current_a),-float(current_b))
            continue
            
        elif routine == 'M':
            manual()
        
        elif routine == 'L':
            load()
            
        elif routine == 'E':
            experimental()
            
        else:
            print("Wrong value, try again")
            continue
        
        run = input('Move again Yes(Y) or No(N)')
        if run == 'Y':
            continue
        if run == 'N':
            GPIO.cleanup()
            break
