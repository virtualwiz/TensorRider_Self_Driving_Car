import socket
from sys import exit
import pygame
import threading
from time import ctime,sleep
import string

# CONFIG
addr=('192.168.31.204',51423)
deadzone = 0.1
# END OF CONFIG

s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

class Car:
    def __init__(self):
        self.speed = 0
        self.acceleration = -2
        self.direction = 0
        self.differential = 40

def Controller_DeadZoneCancellation(rawData):
    if(abs(rawData) <= deadzone):
        rawData = 0
    return rawData

def Range_Limiter(val,range_min,range_max):
    if val > range_max:
        val = range_max
    elif val < range_min:
        val = range_min
    return val

def Controller_ReadAndSend():
    while True:
        pygame.event.pump()
        stickVal_Acc = Controller_DeadZoneCancellation(controller.get_axis(1))
        stickVal_Dir = Controller_DeadZoneCancellation(controller.get_axis(2))
        rider_local.speed += rider_local.acceleration * stickVal_Acc
        rider_local.speed = Range_Limiter(rider_local.speed, -20, 100)
        rider_local.direction = stickVal_Dir * rider_local.differential

        # if controller.get_button(9) == 1:
        #     print("Recording Triggered!")
        #     temp = rider_local.speed
        #     rider_local.speed = -1 # As a signal to start data recording
        #     msgCtrl_Udp = str(rider_local.speed) + "," + str(rider_local.direction)
        #     s.sendto(msgCtrl_Udp.encode('utf-8'), addr)
        #     rider_local.speed = temp
        
        if controller.get_button(9) == 1:
            s.sendto("R".encode('utf-8'), addr)
            print("Recording Triggered!")
            sleep(0.5) #To prevent data congestion

            
        if controller.get_button(6) + controller.get_button(7) == 2:
            print("Brake!")
            rider_local.speed = 0 #Emergency Stop

        if controller.get_button(4) + controller.get_button(5) == 2:
            print("Train!")
            rider_local.speed = 25 #Training Speed

        if controller.get_button(8) == 1:
            s.close()
            exit()
            
        msgCtrl_Udp = str(rider_local.speed) + "," + str(rider_local.direction)
        s.sendto(msgCtrl_Udp.encode('utf-8'), addr)
        print("speed:",round(rider_local.speed,3),"direction",round(rider_local.direction,3))
        sleep(0.15)

pygame.joystick.init()
pygame.display.init()

if pygame.joystick.get_count() == 1:
    controller = pygame.joystick.Joystick(0)
    print("Using controller:",controller.get_name())
elif pygame.joystick.get_count() == 0:
    print("Controller Not Found.")
    exit()
else:
    print("Multiple controllers found.")
    exit()

controller.init()
print("Controller initialized.")

rider_local = Car()
SendThread = threading.Thread(target = Controller_ReadAndSend)
SendThread.start()
