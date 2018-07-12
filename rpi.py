from mvnc import mvncapi as mvnc
import numpy as np
import cv2
import os
import sys
from typing import List
from time import ctime,sleep
from picamera import PiCamera
import io
import RPi.GPIO as gpio
import threading

MOTOR_IO_LEFT = 13
MOTOR_IO_RIGHT = 15
MOTOR_IO_LEFT_REV = 19
MOTOR_IO_RIGHT_REV = 21

MOTOR_PWM_FREQUENCY = 120

BCN_IO_RED = 12
BCN_IO_GREEN = 11
BCN_LIGHT_PERIOD = 0.05
BCN_LIGHT_WAIT = 0.3
BCN_INTERVAL = 10

FRAME_WIDTH = 80
FRAME_HEIGHT = 60
FRAME_FPS = 30

bcnStatus = 0

def flashBeacon():
    if bcnStatus == 0:
        gpio.output(BCN_IO_RED,True)
        gpio.output(BCN_IO_GREEN,True)
        sleep(BCN_LIGHT_PERIOD)
        gpio.output(BCN_IO_GREEN,False)
        sleep(BCN_LIGHT_WAIT)
        gpio.output(BCN_IO_RED,False)
    elif bcnStatus == 1:
        gpio.output(BCN_IO_GREEN,True)
        sleep(BCN_LIGHT_PERIOD)
        gpio.output(BCN_IO_GREEN,False)
    elif bcnStatus == 2:
        gpio.output(BCN_IO_RED,True)
        gpio.output(BCN_IO_GREEN,True)
        sleep(BCN_LIGHT_PERIOD)
        gpio.output(BCN_IO_RED,False)
        gpio.output(BCN_IO_GREEN,False)
        sleep(BCN_LIGHT_WAIT)
        gpio.output(BCN_IO_RED,True)
        sleep(BCN_LIGHT_PERIOD)
        gpio.output(BCN_IO_RED,False)

def setBeaconStatus(status):
    global bcnStatus
    bcnStatus = status


def Range_Limiter(val,range_min,range_max):
    if val > range_max:
        val = range_max
    elif val < range_min:
        val = range_min
    return val

class Car:
    def __init__(self):
        self.speed = 0
        self.direction = 0
        self.pwmDutyLeft = 0
        self.pwmDutyRight = 0

    def writeMotor(self):
        # self.pwmDutyLeft = self.speed + (self.direction * (self.speed / 100))
        # self.pwmDutyRight = self.speed - (self.direction * (self.speed / 100))
        # self.pwmDutyLeft = Range_Limiter(self.pwmDutyLeft, 0, 100)
        # self.pwmDutyRight = Range_Limiter(self.pwmDutyRight, 0, 100)
        self.pwmDutyLeft = self.speed + self.direction
        self.pwmDutyRight = self.speed - self.direction
        self.pwmDutyLeft = Range_Limiter(self.pwmDutyLeft, -100, 100)
        self.pwmDutyRight = Range_Limiter(self.pwmDutyRight, -100, 100)
        # print(self.pwmDutyLeft, self.pwmDutyRight)

        if self.pwmDutyLeft >= 0:
            MotorPwmRevL.ChangeDutyCycle(0)
            MotorPwmL.ChangeDutyCycle(self.pwmDutyLeft)
        elif self.pwmDutyLeft < 0:
            MotorPwmL.ChangeDutyCycle(0)
            MotorPwmRevL.ChangeDutyCycle(-(self.pwmDutyLeft))
        
        if self.pwmDutyRight >= 0:
            MotorPwmRevR.ChangeDutyCycle(0)
            MotorPwmR.ChangeDutyCycle(self.pwmDutyRight)
        elif self.pwmDutyRight < 0:
            MotorPwmR.ChangeDutyCycle(0)
            MotorPwmRevR.ChangeDutyCycle(-(self.pwmDutyRight))


rider = Car()

print("Initializing hardware")
camera = PiCamera()
camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
camera.framerate = FRAME_FPS

gpio.setmode(gpio.BOARD)

gpio.setup(MOTOR_IO_LEFT, gpio.OUT)
gpio.setup(MOTOR_IO_RIGHT, gpio.OUT)
gpio.setup(MOTOR_IO_LEFT_REV, gpio.OUT)
gpio.setup(MOTOR_IO_RIGHT_REV, gpio.OUT)

gpio.setup(BCN_IO_RED, gpio.OUT)
gpio.setup(BCN_IO_GREEN, gpio.OUT)

MotorPwmL = gpio.PWM(MOTOR_IO_LEFT, MOTOR_PWM_FREQUENCY)
MotorPwmR = gpio.PWM(MOTOR_IO_RIGHT, MOTOR_PWM_FREQUENCY)
MotorPwmL.start(0)
MotorPwmR.start(0)

MotorPwmRevL = gpio.PWM(MOTOR_IO_LEFT_REV, MOTOR_PWM_FREQUENCY)
MotorPwmRevR = gpio.PWM(MOTOR_IO_RIGHT_REV, MOTOR_PWM_FREQUENCY)
MotorPwmRevL.start(0)
MotorPwmRevR.start(0)


print("Starting NCS")
devices = mvnc.EnumerateDevices()
if len(devices) == 0:
    print('Error - No devices found')

device = mvnc.Device(devices[0])
device.OpenDevice()


print("Reading graph file")
graph_filename = './ncs.graph'
try :
    with open(graph_filename, mode='rb') as f:
        in_memory_graph = f.read()
except :
    print ("Error reading graph file: " + graph_filename)

print("Downloading graph to NCS")
graph = device.AllocateGraph(in_memory_graph)


def Controller_ReceiveAndWrite():
    while True:
        stream = io.BytesIO()
        camera.capture(stream, format='jpeg', use_video_port=True)
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        image = cv2.imdecode(data, 1)
        image = image[:, :, ::-1]
        image = image.reshape((14400,)).astype(np.float16)
        image = image /  255
        # image = np.zeros((14400,), dtype=np.float16)  //for NCS benchmark only
        if (graph.LoadTensor(image.astype(np.float16), 'user object')):
            output, userobj = graph.GetResult()
            decision = (np.argmax(output) - 7) * 6
        print(decision)

        rider.speed = 5
        rider.direction = decision
        rider.writeMotor()

def Beacon_Write():
    while True:
        flashBeacon()
        sleep(BCN_INTERVAL)

ControlThread = threading.Thread(target = Controller_ReceiveAndWrite)
ControlThread.start()
BeaconThread = threading.Thread(target = Beacon_Write)
BeaconThread.start()