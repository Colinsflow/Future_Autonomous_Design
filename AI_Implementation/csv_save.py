from picarx import Picarx
import time, threading
import csv
# import pygame
# pygame.init()
# joystick = pygame.joystick.Joystick(0)
# joystick.init()
px = Picarx()
px = Picarx(grayscale_pins=['A0', 'A1', 'A2']) 
px.set_grayscale_reference(500)

 
last_state = None
current_state = None
px_power = 10
offset = 35
value4 = 0
offtrack = 0
gm_val_list =[0,0,0]
def read_sensor_values():
    global gm_val_list
    # Replace with actual code to read sensor values
    gm_val_list = px.get_grayscale_data()
    value1 = gm_val_list[0]
    value2 = gm_val_list[1]
    value3 = gm_val_list[2]
    return value1, value2, value3

def getData():
    global value4
    print("getting data")
    # Read sensor values
    value1, value2, value3 = read_sensor_values()
    
    # Get current timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Write sensor data to CSV file
    with open('sensor_data.csv', 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, value1, value2, value3, value4])
    
    #threading.Timer(.2, getData).start()
    
# Open CSV file in append mode and write header
with open('sensor_data.csv', 'a') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'GS1', 'GS2', 'GS3','Steering'])
    
# Loop to continuously write sensor data to CSV file

getData()

def outHandle():
    global last_state, current_state
    if last_state == 'left':
        px.set_dir_servo_angle(-30)
        px.backward(10)
    elif last_state == 'right':
        px.set_dir_servo_angle(30)
        px.backward(10)
    while True:
        gm_val_list = px.get_grayscale_data()
        gm_state = px.get_line_status(gm_val_list)
        print("outHandle gm_val_list: %s, %s"%(gm_val_list, gm_state))
        currentSta = gm_state
        if currentSta != last_state:
            break
    time.sleep(0.001)
def control():
    global value4, gm_val_list, offtrack
    while True:
        getData()
        gm_state = px.get_line_status(gm_val_list)
        print("gm_val_list: %s, %s"%(gm_val_list, gm_state))

        if gm_state != "stop":
            last_state = gm_state

        if gm_state == 'forward':
            px.set_dir_servo_angle(0)
            px.forward(px_power)
            value4 = 0
        elif gm_state == 'left':
            px.set_dir_servo_angle(offset)
            px.forward(px_power)
            value4 = -1
        elif gm_state == 'right':
            px.set_dir_servo_angle(-offset)
            px.forward(px_power)
            value4 = 1
        else:
            offtrack +=1

control()

