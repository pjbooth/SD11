####--------------------------------------------------------
#### Name:            SD11Main.py
#### Programmer:      Paul Booth
#### Created:         04/12/2015
#### Purpose:         Read an IR motion sensor
####--------------------------------------------------------
import time
import RPi.GPIO as GPIO

## Variables and constants
delay = 5					# number of seconds delay between readings
irSensor = 2
lightSensor = 4

## Functions

def printlog(msg)
	print(msg)
	
	
## Initialise
printlog("Initialising")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(irSensor,IN)
GPIO.setup(lightSensor,IN)

## Main loop
printlog("Main loop")
try:
	while True:
		printlog("Reading sensor")
		s = GPIO.input(irSensor)
		printlog("InfraRed sensor = " + str(s))
		time.sleep(delay)
except KeyboardInterrupt:
	printlog("Exiting after Ctrl-C")
	
	


