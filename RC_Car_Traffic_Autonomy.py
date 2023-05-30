'''
    GMU SENIOR DESIGN SPRING 2023
    --Autonomous Driving Program--
    
    Platform:
    
    -Sunfounder Picar-X
    
    Implemented Functionalities:
    
    -Google Firebase Descision Making
    
    -Adafruit 9-AXIS Inertail Measurement Unit Forward Steering Alignment
    
    -Dual IR Wing Sensors For Lane Detection
    
'''
import matplotlib.pyplot as plt
import time, threading
import board
import adafruit_bno055
import numpy as np
from picarx import Picarx
import RPi.GPIO as GPIO
from robot_hat.utils import reset_mcu
from vilib import Vilib
import time as time
from time import sleep, strftime, localtime
import readchar
import pygame
import pyrebase


#configuring Google Firebase Realtime Database 
config = {
    "apiKey" : "*****************",
    "authDomain" : "*****************",
    "databaseURL" : "*****************",
    "storageBucket" : "*****************"
    }

#initialize firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()

reset_mcu()
sleep(0.2)

#initialize pygame and designate PS4 controller
pygame.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

px = Picarx()
i2c = board.I2C()  # I2C communication for 9-AXIS IMU
last_val = 0xFFFF
sampling_rate = 100
sensor = adafruit_bno055.BNO055_I2C(i2c) #9-AXIS sensor

#Pinout of Dual Wing IR sensors and Wheel Encoder
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.setup(4, GPIO.IN)
GPIO.setup(22, GPIO.IN)

innit_angle = 0
last_state = None
current_state = None
px_power = 10
offset = 20
paused = 0
left_wing = 4
right_wing = 17
steer = 0
direction_index = 0
wheel_enc = 22
extra_ticks = 0
fig, ax = plt.subplots()

#for plotting the euler angle during run (causes crash after one run)
ax.set_xlabel('Time (s)')
ax.set_ylabel('Orientation (degrees)')

#Direction array is the instructions at each intersection.
#the first item will be the initial orientation, last instuction terminates run.
#values between first and last indexes are the turns at each intersection it goes through in that path.
#EXAMPLE ARRAY: direction_array = ['south', 'left', 'straight' ,'right','left','straight' ,'end']
direction_array = db.child("overhead").child('path').get().val()

#decode initial orientation
if direction_array[0] == 'north':
    orientation = 1
elif direction_array[0] == 'east':
    orientation = 2
elif direction_array[0] == 'south':
    orientation = 3
elif direction_array[0] == 'west':
    orientation = 0

#Initializing Wheel Encoder Variables
pulse_count = 0
pulse_count2 = 0
total_distance = 0
rounded_distance = 0

#arrays used for plotting euler angles over time
time_values = []
orientation_values = []

#set start time
time_start = time.time()
time_end = 0
velocity = 0

# Interrupt handler for wheel encoder pulses
def pulse_handler(channel):
    global pulse_count, pulse_count2
    pulse_count += 1
    pulse_count2 += 1
    #distance_travel = int(pulse_count * .72)
      

# Set up interrupt on rising edge of pulse from wheel encoder signal wire
GPIO.add_event_detect(wheel_enc, GPIO.RISING, callback=pulse_handler)

#timer interrupt for determining velocity 
def getData():
    global pulse_count2, total_distance, time_start, time_end, velocity, rounded_distance, time_values, orientation_values
    time_end = time.time() #mark time of pulse occurance
    time_diff = time_end - time_start #time between pulses
    distance_calcd = (pulse_count2 /20)*(6.35 * np.pi) #distance traveled for one pulse
    total_distance += distance_calcd #Increment total distance traveled
    velocity = np.around(distance_calcd / time_diff,2) #velocity updated
    rounded_distance = np.around(total_distance,2)
    
    #code for plotting euler angle
    if (sensor.euler[0] is not None): #ensure euler angle provides data
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                if euler_angle >= 0 and euler_angle <= 360:
                    time_values.append(time_end) 
                    orientation_values.append(euler_angle)
    pulse_count2 = 0
    time_start = time_end
    
    db.child("ID6").child("data").update({"distance":rounded_distance}) #update distance to database
    db.child("ID6").child("data").update({"velocity":velocity})
    threading.Timer(.1, getData).start() #set up timer for the interrupt


#this is not implented currently due to inaccuracies
#it will orientate the car to face the initial angle
def Calib_ang():
    global direction_array, orientation
    if orientation == 0:
        innit_angle = 28
    elif orientation == 1:
        innit_angle = 128
    elif orientation == 2:
        innit_angle = 208
    elif orientation == 3:
        innit_angle = 298
    rotate = 'none'
    rotate_cnt = 0
    #tweak for debug
    rotate_sharpness = 100
    rotate_tol = 2
    while True:
    
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                if euler_angle >= innit_angle:
                    rotate = "left"
                elif euler_angle <= innit_angle:
                    rotate = "right"
                if euler_angle <= innit_angle + rotate_tol and euler_angle >= innit_angle - rotate_tol:
                    rotate = "done"
                    initial_straight()
                    
        if rotate == "right":
            if rotate_cnt <= rotate_sharpness:
                px.set_dir_servo_angle(-35)
                px.forward(-5)
            else:
                px.set_dir_servo_angle(35)
                px.forward(5)

               
        elif rotate == "left":
            if rotate_cnt <= rotate_sharpness:
                px.set_dir_servo_angle(35)
                px.forward(-5)
            else:
                px.set_dir_servo_angle(-35)
                px.forward(5)
        else:
            continue
        rotate_cnt +=1
        if rotate_cnt == rotate_sharpness*2 +1:
           rotate_cnt = 0

#this function is called thru each index of the direction array to determine action
def outHandle():
    
    global last_state, current_state, direction_index, orientation

    traff_sense = int(db.child("ID6").child("location").child("traffic sensor").get().val())
    
    print(str(traff_sense) + " traffic Sensor")
    if  traff_sense == 7 or traff_sense == 6 or traff_sense == 11 or traff_sense == 10:
        traffic_read = 1
        
    else:
        traffic_read = 0
        
    immediate_direction = direction_array[direction_index]
    direction_index += 1
    

    if immediate_direction == 'left':
        
        if traffic_read == 0:
            left()
        else:
            left_read(traff_sense)

    elif immediate_direction == 'straight':
        if traffic_read == 0:
            straight_call()
        else:
            straight_read(traff_sense)
    elif immediate_direction == 'right':
        if traffic_read == 0: 
            right()
        else:
            right_read(traff_sense)
    elif immediate_direction == 'end':
        end()
    elif immediate_direction == 'south' or 'north' or 'east' or 'west':
        #Calib_ang()
        db.child("ID6").child("data").update({"Mode":"Autonomous"})
        initial_straight()
    else:
        left()
    
    
           
    #steer the direction until finding the new line

#hardcoded direction of grid for north east south west
def orientate():
    global orientation
    if orientation == 0:
        innit_angle = 30
    elif orientation == 1:
        innit_angle = 115
    elif orientation == 2:
        innit_angle = 207
    elif orientation == 3:
        innit_angle = 301
    return innit_angle

#turning right while coming up to a traffic light 
def right_read(traff_sense):
    global orientation, pulse_count, extra_ticks
    time_stopped = 0
    initial_pulse = 0
    trafficlight_str = '0'
    trigger = "none"
    #(reading from firebase node dependant on orientation and geofenced region
    if orientation == 0:
        #westbound
        if traff_sense == 11:
            #traff 11
            trafficlight_str = "11"
            trigger = "south"
        elif traff_sense == 10:
            #traff 10
            trafficlight_str = "10"
            trigger = "north"
    elif orientation == 1:
        #northbound
        if traff_sense == 10:
            #traff 10
            trafficlight_str = "10"
            trigger = "west"
        elif traff_sense == 6:
            #traff 6
            trafficlight_str = "6"
            trigger = "east"
    elif orientation == 2:
        #eastbound
        if traff_sense == 6:
            #traff 6
            trafficlight_str = "6"
            trigger = "north"
        elif traff_sense == 7:
            #traff 7
            trafficlight_str = "7"
            trigger = "south"
    elif orientation == 3:
        #southbound
        if traff_sense == 7:
            #traff 7
            trafficlight_str = "7"
            trigger = "east"
        elif traff_sense == 11:
            #traff 11 
            trafficlight_str = "11"
            trigger = "west"
    
    
    if orientation == 3:
        orientation = 0
    else:
        orientation +=1
    if orientation == 0:
        boundmin = 22
        boundmax = 28

    elif orientation == 1:
        boundmin = 112
        boundmax = 118
        
    elif orientation == 2:
        boundmin = 202
        boundmax = 208
        
    elif orientation == 3:
        boundmin = 292
        boundmax = 298

    LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
    print(str(LED_STATE)+ "led_state")
    print(trigger)
    if trigger == LED_STATE:
        print("stopped at" + trafficlight_str + "for\n")
        px.stop()
        while True:
            LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
            #print(LED_STATE)
            if LED_STATE == trigger:
                time_stopped+=1
            else:
                print(str(time_stopped) + "ticks")
                time_stopped = 0
                px.forward(5)
                
                break
    
    
    
    print('right read')
    steer = 35
    px.set_dir_servo_angle(steer)
    px.forward(5)
    
    #turn right until reaching the correct orientation
    while True:
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                if euler_angle >= boundmin and euler_angle <= boundmax:
                    print(str(pulse_count - initial_pulse))
                    outHandle()
       
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines()
            px.set_dir_servo_angle(steer)
        
#same as right read but for left turn           
def left_read(traff_sense):
    global orientation, pulse_count, extra_ticks
    time_stopped = 0
    initial_pulse = 0
    trafficlight_str = '0'
    trigger = "none"
   
    if orientation == 0:
        #westbound
        if traff_sense == 11:
            #traff 11
            trafficlight_str = "11"
            trigger = "south"
        elif traff_sense == 10:
            #traff 10
            trafficlight_str = "10"
            trigger = "north"
    elif orientation == 1:
        #northbound
        if traff_sense == 10:
            #traff 10
            trafficlight_str = "10"
            trigger = "west"
        elif traff_sense == 6:
            #traff 6
            trafficlight_str = "6"
            trigger = "east"
    elif orientation == 2:
        #eastbound
        if traff_sense == 6:
            #traff 6
            trafficlight_str = "6"
            trigger = "north"
        elif traff_sense == 7:
            #traff 7
            trafficlight_str = "7"
            trigger = "south"
    elif orientation == 3:
        #southbound
        if traff_sense == 7:
            #traff 7
            trafficlight_str = "7"
            trigger = "east"
        elif traff_sense == 11:
            #traff 11 
            trafficlight_str = "11"
            trigger = "west"
    

    if orientation == 0:
        orientation = 3
    else:
        orientation -=1
    
    if orientation == 0:
        boundmin = 22
        boundmax = 28
        
    elif orientation == 1:
        boundmin = 112
        boundmax = 118
        
    elif orientation == 2:
        boundmin = 202
        boundmax = 208
        
    elif orientation == 3:
        boundmin = 292
        boundmax = 298


    LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
    print(str(LED_STATE)+ "led_state")
    print(trigger)
    if trigger == LED_STATE:
        print("stopped at" + trafficlight_str + "for\n")
        px.stop()
        while True:
            LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
            #print(LED_STATE)
            if LED_STATE == trigger:
                time_stopped+=1
            else:
                print(str(time_stopped) + "ticks")
                time_stopped = 0
                px.forward(5)
                
                break
    print('left read')
    steer = -35
    px.set_dir_servo_angle(steer)
    px.forward(5)
    while True:
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                if euler_angle >= boundmin and euler_angle <= boundmax:
                    print(str(pulse_count - initial_pulse))
                    outHandle()
       
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines()
            px.set_dir_servo_angle(steer)
        
           

#going straight through intersection with traffic light
def straight_read(traff_sense):
    #straight method implemented with orientation global var.
    global orientation, pulse_count, extra_ticks
    print('straight read')
    px.forward(5)
    initial_pulse = pulse_count
    str8_dur = 0
    end = 0
    trigger = "none"
    time_stopped = 0
    trafficlight_str = '0'
    check_pulses = 10
    exit_flag = 0
    innit_angle = None
    innit_angle = orientate()
    if orientation == 0 or orientation == 2:  
        travel_ticks = 45
    else:
        travel_ticks = 43
    
    while (pulse_count - initial_pulse) < check_pulses:
        
        if orientation == 0:
            #westbound
            if traff_sense == 11:
                #traff 11
                trafficlight_str = "11"
                trigger = "south"
            elif traff_sense == 10:
                #traff 10
                trafficlight_str = "10"
                trigger = "north"
        elif orientation == 1:
            #northbound
            if traff_sense == 10:
                #traff 10
                trafficlight_str = "10"
                trigger = "west"
            elif traff_sense == 6:
                #traff 6
                trafficlight_str = "6"
                trigger = "east"
        elif orientation == 2:
            #eastbound
            if traff_sense == 6:
                #traff 6
                trafficlight_str = "6"
                trigger = "north"
            elif traff_sense == 7:
                #traff 7
                trafficlight_str = "7"
                trigger = "south"
        elif orientation == 3:
            #southbound
            if traff_sense == 7:
                #traff 7
                trafficlight_str = "7"
                trigger = "east"
            elif traff_sense == 11:
                #traff 11 
                trafficlight_str = "11"
                trigger = "west"
        
        LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
        print(LED_STATE)
        if trigger == LED_STATE:
            print("stopped at" + trafficlight_str + "for\n")
            px.stop()
            while True:
                LED_STATE = db.child("Lights").child(trafficlight_str).get().val()
                #print(LED_STATE)
                if LED_STATE == trigger:
                    time_stopped+=1
                else:
                    print(str(time_stopped) + "ticks")
                    time_stopped = 0
                    px.forward(5)
                    print(str(pulse_count - initial_pulse))
                    extra_ticks = check_pulses - (pulse_count - initial_pulse)
                    exit_flag = 1
                    break
            if exit_flag == 1:
                break
        
   
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines_fwd()    
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:    
                #db.child("traxxas").child("ID5").update({"Orientation":sensoreuler})
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(extra_ticks) + "extra ticks")
    #ensures the correct amount of distance is traveled
    while (pulse_count - initial_pulse) < travel_ticks + extra_ticks:
        #if dual wing sensor tripped
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines_fwd()  #return to middle of road
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:    
                
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(pulse_count - initial_pulse))
    outHandle()                          
#going straight through an intersection without a traffic light
def straight_call():
    #straight method implemented with orientation global var.
    global orientation, pulse_count
    print('straight call')
    px.forward(5)
    initial_pulse = pulse_count
    str8_dur = 0
    end = 0
    innit_angle = None
    innit_angle = orientate()
    if orientation == 0 or orientation == 2:    
        travel_ticks = 47
    else:
        travel_ticks = 42
    while (pulse_count - initial_pulse) < travel_ticks:
   
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines_fwd()    
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:    
                #db.child("traxxas").child("ID5").update({"Orientation":sensoreuler})
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(pulse_count - initial_pulse))
    outHandle()           
#called after a left or right turn to complete the remaining distance of the road
def straight():
    #straight method implemented with orientation global var.
    global orientation, pulse_count
    print('straight')
    px.forward(5)
    initial_pulse = pulse_count
    str8_dur = 0
    end = 0
    innit_angle = None
    innit_angle = orientate()
    
    if orientation == 0 or orientation == 2:  
        travel_ticks = 8
    else:
        travel_ticks = 6
    while (pulse_count - initial_pulse) <= travel_ticks :
        #end = db.child("traxxas").child("end").get()
        #print(end.val())
        #if end.val() == 1:
        #    outHandle()
        
        
             
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines_fwd()
                
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:
                #db.child("traxxas").child("ID5").update({"Orientation":sensoreuler})   
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(pulse_count - initial_pulse)+"total ticks after read")
    outHandle()
#called for the first instance of direction array to start moving forward
def initial_straight():
    #straight method implemented with orientation global var.
    global orientation, pulse_count
    print('initial straight')
    px.forward(5)
    initial_pulse = pulse_count
    str8_dur = 0
    end = 0
    innit_angle = None
    innit_angle = orientate()
    if orientation == 0 or orientation == 2:  
        travel_ticks = 35
    else:
        travel_ticks = 25
    while (pulse_count - initial_pulse) <= travel_ticks :
        #end = db.child("traxxas").child("end").get()
        #print(end.val())
        #if end.val() == 1:
        #    outHandle()
             
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines_fwd()
                
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:
                #db.child("traxxas").child("ID5").update({"Orientation":sensoreuler})   
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(pulse_count - initial_pulse)+"initial tick")
    outHandle()
#finishes movement at end of path
def end():
    #straight method implemented with orientation global var.
    global orientation, pulse_count, time_values, orientation_values
    print('end')
    px.forward(5)
    initial_pulse = pulse_count
    str8_dur = 0
    end = 0
    innit_angle = None
    innit_angle = orientate()
    if orientation == 0 or orientation == 2:  
        travel_ticks = 25
    else:
        travel_ticks = 20
    while (pulse_count - initial_pulse) <= 20 :
  
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines()
                
        #euler angle consistency
        if (sensor.euler is not None):
            sensoreuler = sensor.euler[0]
            if sensoreuler is not None:
                #db.child("traxxas").child("ID5").update({"Orientation":sensoreuler})   
                if int(innit_angle - sensoreuler) >= 2:
                    px.set_dir_servo_angle(10)
                elif int(innit_angle - sensoreuler) >= 1:
                    px.set_dir_servo_angle(5)
                elif int(innit_angle - sensoreuler) <= -2:
                    px.set_dir_servo_angle(-10)
                elif int(innit_angle - sensoreuler) <= -1:
                    px.set_dir_servo_angle(-5)
                else:
                    px.set_dir_servo_angle(0)
    print(str(pulse_count - initial_pulse))
    px.stop()
    ax.plot(time_values, orientation_values)
    plt.show()
    manual_control()
#left through an intersection without traffic light
def left():
    global orientation, pulse_count
    initial_pulse = 0
    if orientation == 0:
        orientation = 3
    else:
        orientation -=1
    if orientation == 0:
        boundmin = 22
        boundmax = 28
        
    elif orientation == 1:
        boundmin = 112
        boundmax = 118
        
    elif orientation == 2:
        boundmin = 202
        boundmax = 208
        
    elif orientation == 3:
        boundmin = 292
        boundmax = 298
        
    print('left')
    steer = -35
    px.set_dir_servo_angle(steer)
    px.forward(5)
    while True:
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                #db.child("traxxas").child("ID5").update({"Orientation":euler_angle})
                if euler_angle >= boundmin and euler_angle <= boundmax:
                    print(str(pulse_count - initial_pulse))
                    straight()
        #print(euler_angle)
            
        #db.child("pi").update({"euler":euler_angle})
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines()
            px.set_dir_servo_angle(steer)
        
            #db.child("pi").update({"orientation":orientation})
        
        #gm_val_list = px.get_grayscale_data()
        #gm_state = px.get_line_status(gm_val_list)
        #if gm_state != 'stop':

#right through an intersection without traffic light
def right():
    global orientation, pulse_count
    initial_pulse = 0
    
    print('right')
    steer = 35
    px.set_dir_servo_angle(steer)
    px.forward(5)
    
    if orientation == 3:
        orientation = 0
    else:
        orientation +=1
    if orientation == 0:
        boundmin = 22
        boundmax = 28

    elif orientation == 1:
        boundmin = 112
        boundmax = 118
        
    elif orientation == 2:
        boundmin = 202
        boundmax = 208
        
    elif orientation == 3:
        boundmin = 292
        boundmax = 298
    while True:
        
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
#                 db.child("traxxas").child("ID5").update({"Orientation":euler_angle})
                if euler_angle >= boundmin and euler_angle <= boundmax:
                    print(str(pulse_count - initial_pulse))
            #db.child("pi").update({"orientation":orientation})
                    straight()
        #print(euler_angle)
        #db.child("pi").update({"euler":euler_angle})
        if GPIO.input(left_wing) == 1 or GPIO.input(right_wing) == 1:
            escapelines()
            px.set_dir_servo_angle(steer)
#go to middle of the road when wing sensors are detecting black (called when turning)
def escapelines():
    while GPIO.input(left_wing) != 0:
        px.set_dir_servo_angle(5)
        px.forward(5)

    while GPIO.input(right_wing) != 0:
        px.set_dir_servo_angle(-5)
        px.forward(5)
    px.forward(5)
#go to middle of the road when wing sensor detects black (called when going straight)
def escapelines_fwd():
    while GPIO.input(left_wing) != 0:
        px.set_dir_servo_angle(20)
        

    while GPIO.input(right_wing) != 0:
        px.set_dir_servo_angle(-20)
        
    px.forward(5)   

#manual mode using PS4 Controller
def manual_control():
    global direction_index, orientation, direction_array, distance_travel
    orientation = 0
    movement = 0
    speed = 0
    picture = 0
    status = 'stop'
    gear = 0
    oldgear = 0
    direction_index = 0
    db.child("ID6").child("data").update({"Mode":"Manual"})
    sleep(1)  # wait for startup

    while True:
        
        if (sensor.euler[0] is not None):
            euler_angle = sensor.euler[0]
            if (euler_angle is not None):
                 db.child("ID6").child("data").update({"Orientation":euler_angle})
#         print("\rstatus: %s , speed: %s    "%(status, speed), end='', flush=True)
        pygame.event.get()
        # Get the value of the left joystick's x-axis
        x_axis = joystick.get_axis(0) #steering axis
        #y_axis = -joystick.get_axis(0)
        lt_throttle = joystick.get_axis(2) #left throttle  axis
        rt_throttle = joystick.get_axis(5) #right throttle acis
        servo_horiz_axis = joystick.get_axis(4)
        servo_verti_axis = joystick.get_axis(3)
        
        # Set the servo's angle based on the x-axis value
        #servo.ChangeDutyCycle(7.5 + x_axis)
        px.set_dir_servo_angle(x_axis*35)
        px.set_camera_servo1_angle(servo_verti_axis*35)
        px.set_camera_servo2_angle(-servo_horiz_axis*35)
        # Get the value of the A button
        b_button = joystick.get_button(0)
        rt_button = joystick.get_button(8)
        lt_button = joystick.get_button(7)
        c_button = joystick.get_button(9)
        # If the A button is pressed, increase the motor's speed
        if lt_throttle > -.99:
            movement -= ((lt_throttle+1))
            #print('lt')
            gear = 2
        elif rt_throttle > -.99:
            movement += ((rt_throttle+1))
            #print('rt')
            gear = 1
     
        else:
            gear = 0
            
            #uncomment for hardcoded momentum
            #if movement < -12:
            #    movement += .9
            #elif movement > 12:
            #    movement -= .9 #coast value
            #elif movement <= -.4:
            #    movement += .4
            #elif movement >= .4:
            #    movement -= .4
            #if movement <= .4 and movement >= -.4:
            movement = 0
        if movement >= 65:
            movement = 65
        if movement <= -65:
            movement = -65

        if b_button: #pressing the X button begins automonous mode
            movement = 0
            direction_array = db.child("overhead").child('path').get().val()
            if direction_array[0] == 'north':
                orientation = 1
            elif direction_array[0] == 'east':
                orientation = 2
            elif direction_array[0] == 'south':
                orientation = 3
            elif direction_array[0] == 'west':
                orientation = 0
            outHandle()
# #         if c_button:
        
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                
                if event.button == 3:
                    outHandle()
                    
                if event.button == 10: 
                    
                    _time = strftime('%Y-%m-%d-%H-%M-%S',localtime(time()))
                    name = 'photo_%s'%_time
                    path = "/home/pi/Pictures/picar-x/"
                    Vilib.take_photo(name, path)
                    print('\nphoto save as %s%s.jpg'%(path,name))
                    gear = 3
           
           
            
    
        px.forward(movement*.5)
        #if gear != oldgear:
            #for taillights
            #db.child("pi").update({"movement_state":gear})
            
        oldgear = gear

#begining of code
if __name__=='__main__':
    try:
       
        while sensor.calibration_status[3] != 3: #calibrate the 9-AXIS IMU
            print(sensor.calibrated)
            print(sensor.calibration_status)
        sleep(2)
        
        getData()
        manual_control()
        

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        px.stop()
    except TypeError:
        print("TypeError")
        px.stop()
    except Exception as e:
        print(e)
        print('manual control')
        px.stop()
    finally:
        print('manual control')
        manual_control()






