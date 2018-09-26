import RPi.GPIO as io
import socket
import threading
from picamera import PiCamera
from time import ctime,sleep
import os

addr=('',51423)
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(addr)

MOTOR_IO_LEFT = 13
MOTOR_IO_RIGHT = 15
MOTOR_IO_LEFT_REV = 19
MOTOR_IO_RIGHT_REV = 21

MOTOR_PWM_FREQUENCY = 120

BCN_IO_RED = 12
BCN_IO_GREEN = 11
BCN_LIGHT_PERIOD = 0.05
BCN_LIGHT_WAIT = 0.3
BCN_INTERVAL = 3

FRAME_WIDTH = 80
FRAME_HEIGHT = 60
FRAME_FPS = 30

bcnStatus = 0
loggerStatus = False

camera = PiCamera()
camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
camera.framerate = FRAME_FPS

io.setmode(io.BOARD)

io.setup(MOTOR_IO_LEFT, io.OUT)
io.setup(MOTOR_IO_RIGHT, io.OUT)
io.setup(MOTOR_IO_LEFT_REV, io.OUT)
io.setup(MOTOR_IO_RIGHT_REV, io.OUT)

io.setup(BCN_IO_RED, io.OUT)
io.setup(BCN_IO_GREEN, io.OUT)

MotorPwmL = io.PWM(MOTOR_IO_LEFT, MOTOR_PWM_FREQUENCY)
MotorPwmR = io.PWM(MOTOR_IO_RIGHT, MOTOR_PWM_FREQUENCY)
MotorPwmL.start(0)
MotorPwmR.start(0)

MotorPwmRevL = io.PWM(MOTOR_IO_LEFT_REV, MOTOR_PWM_FREQUENCY)
MotorPwmRevR = io.PWM(MOTOR_IO_RIGHT_REV, MOTOR_PWM_FREQUENCY)
MotorPwmRevL.start(0)
MotorPwmRevR.start(0)

def flashBeacon():
    if bcnStatus == 0:
        io.output(BCN_IO_RED,True)
        sleep(BCN_LIGHT_WAIT)
        io.output(BCN_IO_RED,False)
    elif bcnStatus == 1:
        io.output(BCN_IO_GREEN,True)
        sleep(BCN_LIGHT_PERIOD)
        io.output(BCN_IO_GREEN,False)
    elif bcnStatus == 2:
        io.output(BCN_IO_RED,True)
        io.output(BCN_IO_GREEN,True)
        sleep(BCN_LIGHT_PERIOD)
        io.output(BCN_IO_RED,False)
        io.output(BCN_IO_GREEN,False)
        sleep(BCN_LIGHT_WAIT)
        io.output(BCN_IO_RED,True)
        sleep(BCN_LIGHT_PERIOD)
        io.output(BCN_IO_RED,False)

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
logText = "N/A"

def Controller_ReceiveAndWrite():
    global loggerStatus
    global logText

    while True:
        data,addr = s.recvfrom(2048)
        data = str(data)
        # print(data)
        if rider.speed > 0 and loggerStatus == False:
            setBeaconStatus(2)
        elif rider.speed == 0 and loggerStatus == False:
            setBeaconStatus(1)

        if data == "R":
            if loggerStatus == False:
                loggerStatus = True
            else:
                loggerStatus = False
            
        else:
            rider.speed = int(float(data[0:data.find(r',')]))
            rider.direction = int(float(data[data.find(r',') + 1:-1] + data[-1]))
            logText = str(rider.direction)
            rider.writeMotor()
        sleep(0.1)

def Beacon_Write():
    while True:
        flashBeacon()
        sleep(BCN_INTERVAL)

def Logger():
    global loggerStatus
    global logText
    while True:
        if loggerStatus == True:
            setBeaconStatus(0)
            logFile = open('/mnt/pdisk/steer_log.txt', 'w')
            # for filename in camera.capture_continuous('/home/pi/img/{counter:06d}.jpg', use_video_port=True):
            for filename in camera.capture_continuous('/mnt/pdisk/{counter:06d}.jpg', use_video_port=True):
                # print('Captured %s' % filename)
                logFile.write(logText)
                logFile.write("\r\n")
                sleep(0.05)
                if loggerStatus == False:
                    logFile.close( )
                    break
        sleep(0.1)

ControlThread = threading.Thread(target = Controller_ReceiveAndWrite)
ControlThread.start()
BeaconThread = threading.Thread(target = Beacon_Write)
BeaconThread.start()
LoggerThread = threading.Thread(target = Logger)
LoggerThread.start()