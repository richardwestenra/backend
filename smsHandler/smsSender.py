#!/usr/bin/python
import os
import sys
import requests
import psycopg2
from twilio.rest import TwilioRestClient
from twilio.rest.exceptions import TwilioRestException

########################################################
# must pass db name as first argument
########################################################


account_sid = os.environ['TWILIO_ACCOUNT_SID'] # Your Account SID from www.twilio.com/console
auth_token  = os.environ['TWILIO_AUTH_TOKEN']  # Your Auth Token from www.twilio.com/console
twilio_number = os.environ['TWILIO_NUMBER']

try:
	conn = psycopg2.connect("dbname={0} user='carpool_match_engine'".format(sys.argv[1]))
except:
	print ("I am unable to connect to the database")
	exit

cur = conn.cursor()
cur.execute("""SELECT id, recipient, body from carpoolvote.outgoing_sms where status='Pending' order by created_ts asc """)

rows = cur.fetchall()

client = TwilioRestClient(account_sid, auth_token)

for row in rows:
	print (row[1] + ' ' + row[2] + '\n')
	phone_number = row[1].replace("-","").replace(" ", "").replace("(", "").replace(")", "").replace(".", "")
	print (phone_number)
	try:
		message = client.messages.create(body=row[2], to=phone_number, from_=twilio_number)
		print(message.sid)

		cur.execute("""UPDATE carpoolvote.outgoing_sms
						SET status='Sent', emission_info = %s 
						WHERE id = %s""", (message.sid, row[0],))
		conn.commit()
	except TwilioRestException as err:
		cur.execute("""UPDATE carpoolvote.outgoing_sms
						SET status='Failed', emission_info = %s 
						WHERE id = %s""", ("{0}".format(err), "{0}".format(row[0]), ))
		conn.commit()
	
cur.close()
conn.close()


