####--------------------------------------------------------
#### Name:            SD11Main.py
#### Programmer:      Paul Booth
#### Created:         04/12/2015
#### Purpose:         Read an IR motion sensor and light level
####--------------------------------------------------------
import os
import subprocess
import sys
import time, datetime
import RPi.GPIO as GPIO
import paho.mqtt.client as paho        #as instructed by http://mosquitto.org/documentation/python/
import ibmiotf.device
import psutil
import math

## Variables and constants
irSensor = 17
lightSensor = 18
lastState = 0
thisState = 0
progname = sys.argv[0]						# name of this program
version = "2.2.12"								# allows me to track which release is running
interval = 15								# number of seconds between readings 
iotfFile = "/home/pi/SD11IOTF.cfg"
dateString = '%Y/%m/%d %H:%M:%S'
mqtt_connected = 0
diagnostics = 1
error_count = 0
error_limit = 20
movement_count = 0
light_count = 0
reading_count = 0 
loop_limit = 5						# number of readings (the reporting interval)



## Functions

def printlog(message):
	logline = progname + " " + version + " " + str(datetime.datetime.now()) + ": " + message
	print logline	
	if mqtt_connected == 1 and diagnostics == 1:
		myData={'name' : progname, 'version' : version, 'date' : str(datetime.datetime.now()), 'message' : message}
		client.publishEvent(event="logs", msgFormat="json", data=myData)


def printdata():
	global movement_count, light_count, reading_count
	light_average = round(light_count / reading_count)
	cputemp = getCPUtemperature()				# may as well report on various processor stats while we're at it
	cpupct = float(psutil.cpu_percent())
	cpumem = float(psutil.virtual_memory().percent)
	myData = {'date' : str(datetime.datetime.now()), 'movements' : movement_count, 'light' : light_average, 'cputemp' : cputemp, 'cpupct' : cpupct, 'cpumem' : cpumem}
	vizData = {'d' : myData}
	client.publishEvent(event="data", msgFormat="json", data=myData)


def myCommandCallback(cmd):						# callback example from IOTF documentation
	printlog("Command received: " + cmd.command + " with data: %s" % cmd.data)
	if cmd.command == "dkE20s*r19s!u":
		reboot()
	elif cmd.command == "gsYi21lu-!e8":
		shutdown()
	else:
		printlog("Unsupported command: %s" % cmd.command)
	return 0


def shutdown():
	command = "/usr/bin/sudo /sbin/shutdown -h now"
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output = process.communicate()[0]
	print output
	return 0


def reboot():
	command = "/usr/bin/sudo /sbin/shutdown -r now"
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output = process.communicate()[0]
	print output
	return 0


                                      
def getCPUtemperature():			# Return CPU temperature as a float
	res = os.popen('vcgencmd measure_temp').readline()
	cputemp = float(res.replace("temp=","").replace("'C\n",""))
	return cputemp


def lightLevel(light_pin):
	reading = 0
	max_read = 101						# need to put a limit on the number of reads otherwise it can last tens of minutes
	GPIO.setup(light_pin, GPIO.OUT)
	GPIO.output(light_pin, GPIO.LOW)
	time.sleep(0.1)
	starttime = time.time()			# note start time
	GPIO.setup(light_pin, GPIO.IN)
	while (GPIO.input(light_pin) == GPIO.LOW) and (reading < max_read):
		reading += 1 
	if reading < max_read:
		endtime = time.time() 			# note end time
		total_time = 1000 * (endtime - starttime) 
		light_level = 80 - (9.5 * math.log(total_time))
	else:
		light_level = 0
	return light_level                           # subjective light level

## Initialise 
printlog("Initialising") 
GPIO.setmode(GPIO.BCM) 
GPIO.setwarnings(False) 
GPIO.setup(irSensor, GPIO.IN) 
GPIO.setup(lightSensor,GPIO.IN) 
lastState = GPIO.input(irSensor)

## Main loop 
printlog("Trying to connect MQ") 

try:
	deviceOptions = ibmiotf.device.ParseConfigFile(iotfFile)	# keeping the IOTF config file locally on device for security

	try:     									# Create the MQTT client, connect to the IOTF broker and start threaded loop in background
		global client
		client = ibmiotf.device.Client(deviceOptions)
		client.connect()
		mqtt_connected = 1
		client.commandCallback = myCommandCallback
		printlog("Established connection with IOTF")

		try:
			while True:
				while reading_count < loop_limit:
					reading_count += 1
					thisState = GPIO.input(irSensor)
					if lastState == 0 and thisState == 1:
						movement_count += 1								# increment the count of the number of discrete movements sensed in this period
					lastState = thisState
					light_count += lightLevel(lightSensor)				# add the latest light level to the cumulative total ffor this period
					time.sleep(interval)
				printdata()
				movement_count = 0
				light_count = 0
				reading_count = 0 

		except KeyboardInterrupt:
			printlog("Exiting after Ctrl-C")

		except BaseException as e:
			printlog("Unexpected fault occurred in main loop: " + str(e))

	except ibmiotf.ConnectionException as e:
		printlog("Cannot start MQTT client and connect to MQ broker. Exception was: " + str(e))
except:
	printlog("Unable to process configuration file " + iotfFile)

finally:
	if error_count < error_limit:
		printlog("Closing program as requested")
	else:
		printlog("Closing program due to excessive errors")
	GPIO.cleanup()		# this ensures a clean exit	



