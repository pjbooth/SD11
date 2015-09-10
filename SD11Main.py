####--------------------------------------------------------
#### Name:            SendLocalIP.py
#### Programmer:      Tony Tosi
#### Created:         09/10/2012
#### Purpose:         Send a text message to ashow it's working
####--------------------------------------------------------
import time
import commands
import re
import smtplib

####--[CONFIGURATION]
server = 'smtp.gmail.com' #smtp server address
server_port = '587' #port for smtp erver

username = 'pjb.rpi@gmail.com' #gmail account
password = 'gmailpass9' #password for that gmail account

fromaddr = 'pjb.rpi@gmail.com' #address to send from
toaddr = 'paulbooth46@gmail.com' #address to send IP to
message = 'RPi SD11 is up and running the main program' #message that is sent
####--[/CONFIGURATION]

headers = ["From: " + fromaddr,
           "To: " + toaddr,
           "MIME-Version: 1.0",
           "Content-Type: text/html"]
headers = "\r\n".join(headers)

server = smtplib.SMTP(server + ':' + server_port)  
server.ehlo()
server.starttls()  
server.ehlo()
server.login(username, password)  
server.sendmail(fromaddr, toaddr, headers + "\r\n\r\n" +  message)  
server.quit()