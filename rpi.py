from mvnc import mvncapi as mvnc
import numpy as np
import cv2
import os
import sys
from typing import List
import time
from picamera import PiCamera
import io
import RPi.GPIO as gpio
import threading

FRAME_WIDTH = 80
FRAME_HEIGHT = 60
FRAME_FPS = 30

print("Initializing camera")
camera = PiCamera()
camera.resolution = (FRAME_WIDTH, FRAME_HEIGHT)
camera.framerate = FRAME_FPS


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

counter=0

while True:
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg', use_video_port=True)
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(data, 1)
    image = image[:, :, ::-1]
    image = image.reshape((14400,)).astype(np.float16)
    image = image /  255

    # image = np.zeros((14400,), dtype=np.float16)

    if (graph.LoadTensor(image.astype(np.float16), 'user object')):
        output, userobj = graph.GetResult()
    print(output)
    counter=counter+1
    print(counter)

graph.DeallocateGraph()
device.CloseDevice()