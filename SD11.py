#!/usr/bin/env python2.7
# Light and Temperature watcher
# Monitors incoming emails for strictly limited range of instructions, from authorised senders only
# based on example from Raspberry Pi Temperature and Light Sensor.pdf 
# By Paul Booth 2015  paul_booth_uk@hotmail.com
#
# This script should automatically detect your 1-wire sensors
# It will load device drivers for them if needed
# Just wire them up and run it
# By Alex Eames http://RasPi.TV

delay = 600                #  number of seconds between each reading sample
dateString = '%Y/%m/%d %H:%M:%S'
diagnostics = 0
datafile = 'IOTWatch1.csv'
emailfrom = "pjb.rpi@gmail.com"
emailto = "paulbooth46@gmail.com"
fileToSend = datafile
username = emailfrom
password = "gmailpass9"
keep_running = 1



import subprocess
import os
import sys
import time, datetime
import RPi.GPIO as GPIO
import smtplib
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText




####  here are the defs   ###################


def read_temp(device):
    DS18b20 = open(device)
    text = DS18b20.read()
    DS18b20.close()

    # Split the text with new lines (\n) and select the second line.
    secondline = text.split("\n")[1]

    # Split the line into words, referring to the spaces, and select the 10th word (counting from 0).
    temperaturedata = secondline.split(" ")[9]

    # The first two characters are "t=", so get rid of those and convert the temperature from a string to a number.
    temperature = float(temperaturedata[2:])

    # Put the decimal point in the right place and display it.
    temperature = temperature / 1000
    return temperature


def msr_time(msr_pin):
    reading = 0
    GPIO.setup(msr_pin, GPIO.OUT)
    GPIO.output(msr_pin, GPIO.LOW)
    time.sleep(0.1)
    starttime = time.time()                     # note start time
    GPIO.setup(msr_pin, GPIO.IN)
    while (GPIO.input(msr_pin) == GPIO.LOW):
        reading += 1
    endtime = time.time()                       # note end time
    total_time = 1000 * (endtime - starttime)
    return total_time                           # reading in milliseconds


def printlog(message):
	logline = datetime.datetime.now().strftime(dateString) + " " + message
	print logline	
	if diagnostics ==1:
#		client.publish(topicLog, payload=logline, qos=0, retain=False)


def logdata(light, temp):
	m = datetime.datetime.now().strftime('%Y/%m/%d') + "," + datetime.datetime.now().strftime('%H:%M:%S') + "," + light + "," + temp
	try:
		f = open(datafile,'a')
		# printlog("File opened for append OK")
	except:
		printlog("Error trying to open file")
	try:
		f.write(m + "\n")
	except:
		printlog("Error trying to write line to datafile")
	f.close()


def diagon():
	global diagnostics
	diagnostics = 1
	print "turning diag on"


def diagoff():
	global diagnostics
	diagnostics = 0
	print "turning diag off"


def sendIOTfile():
	print "requested to send data file"
	send_mime()


def endprog():
	keep_running = 0

def send_mime():
	msg = MIMEMultipart()
	msg["From"] = emailfrom
	msg["To"] = emailto
	msg["Subject"] = "Watcher data file"
	msg.preamble = "This is the data file for the temperature and light level"
	fp = open(fileToSend)
	# Note: we should handle calculating the charset
	attachment = MIMEText(fp.read())
	fp.close()
	newfname = "Watcher " + datetime.datetime.now().strftime(dateString) + ".csv"
	attachment.add_header("Content-Disposition", "attachment", filename=newfname)
	msg.attach(attachment)
	server = smtplib.SMTP("smtp.gmail.com:587")
	server.starttls()
	server.login(username,password)
	server.sendmail(emailfrom, emailto, msg.as_string())
	server.quit()

def parse_email():
	server = smtplib.SMTP("smtp.gmail.com:587")
	server.starttls()
	server.login(username,password)
	server.list()    # Gives list of folders or labels in gmail
	server.quit()
	
	count = 0

    while count < 6:
        try:
            # Connect to inbox
            server.select("inbox"); 

            # Search for an unread email from user's email address
            result, data = server.search(None,'(UNSEEN FROM "paulbooth46@gmail.com")');

            ids = data[0]   # data is a list
            id_list = ids.split() # ids is a space separated string

            latest_email_id = id_list[-1] # get the latest
            result, data = server.fetch(latest_email_id, "(RFC822)");

            raw_email = data[0][1];

            recv_msg = email.message_from_string(raw_email)

            if(recv_msg['Subject'] == "Tester"):
                print("Tester spotted. Hurray!!!")
            else:
                print("I do not understand")
                
            count = 6

        except IndexError:
            time.sleep(30*1)
            if count < 5:
                count = count + 1
                continue
            else:
                print("Sorry,No reply in the last 3 minutes.")
                count = 6

#####################  >>>>>>>>>>>>>>  paused here ;  need to finish from the example

###########  end of defs  ##################

requests = {0 : badrequest,
			1 : diagon,
			2 : diagoff,
			3 : sendIOTfile
			4 : endprog
}


GPIO.setmode(GPIO.BCM) 
GPIO.setup(23, GPIO.OUT) # 23 for LDR light sensor


try:
    w1_devices = os.listdir("/sys/bus/w1/devices/")
except:
    print "Loading 1-wire device drivers, please wait five seconds..."
    output_mp1 = subprocess.Popen('sudo modprobe w1-gpio', shell=True, stdout=subprocess.PIPE)
    output_mp2 = subprocess.Popen('sudo modprobe w1-therm', shell=True, stdout=subprocess.PIPE)
    time.sleep(5)        # wait a few seconds to stop the program storming ahead and crashing out
    w1_devices = os.listdir("/sys/bus/w1/devices/")

no_of_devices = len(w1_devices) -1
print("You have %d 1-wire devices attached" % (no_of_devices))

if no_of_devices < 1:
    print("Please check your wiring and try again.")
    sys.exit()

w1_device_list = []

for device in w1_devices:
    if not ('w1_bus' in device):
        # create string for calling each device and append to list
        this_device = "/sys/bus/w1/devices/" + device + "/w1_slave"
        w1_device_list.append(this_device)


try:
	while keep_running == 1:
            sensor = 1
            for device in w1_device_list:
                temperature = '%d' % read_temp(device)
                sensor += 1
            light = '%.2f' % (5 / msr_time(23))
            msgline = light + " " + temperature
            printlog(msgline)
            logdata(light, temperature)
            parse_email()			# check gmail for incoming emails
            time.sleep(delay)
            
            
    	
except KeyboardInterrupt:
	printlog("Exiting after Ctrl-C")
	
except:
	printlog("Unexpected fault occurred in main loop")
	
finally:
	GPIO.cleanup()     # this ensures a clean exit	

