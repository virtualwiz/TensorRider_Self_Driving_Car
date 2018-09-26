#!/bin/bash
./mjpg_streamer -o "output_http.so -w ./www"  -i "input_raspicam.so -x 80 -y 60 -fps 30"

