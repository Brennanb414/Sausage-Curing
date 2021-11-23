import socket
import re
import datetime
import sys
from pyHS100 import SmartPlug
import sqlite3
import traceback

#static IPs in your router
DEHUMIDIFIER_IP = "192.168.1.61"
FRIDGE_IP = "192.168.1.62"
HUMIDIFIER_IP = "192.168.1.63"

SQLITE_DB_FILENAME = "db.sqlite"

MIN_TEMP = 50
MAX_TEMP = 60

MIN_HUMIDITY = 70
MAX_HUMIDITY = 80

#controls when the humidifier/dehumidifier can turn on/off after the other one has been running
HUMIDITY_INTERVAL = 5 #minutes

#how long before humidifier/dehumid can turn on after the compressor has been on
#needed because the compressor generally tanks the humidity and takes a while to get back to normal
COMPRESSOR_INTERVAL = 10 #minutes

#sqlite setup - create db/connect to it and set up cursor
def create_db_and_data_table():
	conn = sqlite3.connect(SQLITE_DB_FILENAME)
	conn.isolation_level = None
	cur = conn.cursor()
	cur.execute(
	"""CREATE TABLE IF NOT EXISTS "DataPoints" (
		"id"	INTEGER NOT NULL,
		"Humidity"	INTEGER,
		"Temperature(F)"	INTEGER,
		"Time"	INTEGER,
		"insert_time"	INTEGER DEFAULT CURRENT_TIMESTAMP,
		"humidifier_state"	TEXT,
		"dehumidifier_state"	TEXT,
		"fridge_state"	TEXT,
		PRIMARY KEY("id" AUTOINCREMENT)
	);""")
	return cur

#receives data as a udp message, formatted like: "Humidity: ##.# | Temperature(F): ##.# | Time: ######"
def receive_data():
	#reset data dict
	data_dict.clear()
	#wait for message from client
	message = server_socket.recv(1024).decode('UTF-8')
	print(message)
	#for every data point store it in the data_dict
	for data in message.split('|'):
		data = data.replace(" ","")
		colon_idx = data.index(":")
		data_dict.update({data[0:colon_idx]:data[colon_idx+1:-1]})
	return data_dict

def insert_records(data_dict, plugs):
	try:
		sql_insert = f"INSERT INTO DataPoints (Humidity,'Temperature(F)',Time, humidifier_state, dehumidifier_state, fridge_state) VALUES({data_dict['Humidity']},{data_dict['Temperature(F)']},{data_dict['Time']}, '{plugs['humidifier'].state}', '{plugs['dehumidifier'].state}', '{plugs['fridge'].state}')"
		cur.execute(sql_insert)
	except:
		print("ERROR: Data received could not be inserted CHECK SENSOR CONNECTION!, insert failed - received:")
		print(data_dict)
		change_plug(plugs["dehumidifier"], "off", "No sensor connection, turning dehumidifier off")
		change_plug(plugs["humidifier"], "off", "No sensor connection, turning humidifier off")
		#would rather it be cold/on than heat up
		change_plug(plugs["fridge"], "on", "No sensor connection, turning fridge on") 
		#TODO: add push notifications here
		traceback.print_exc()
	
#changes a plug to the specified state and returns true if successful
def change_plug(plug, state, msg_if_successful=None):
	if(state.upper() == "ON" and plug.state == "OFF"):
		plug.turn_on()
	elif(state.upper() == "OFF" and plug.state == "ON"):
		plug.turn_off()
	else:
		return False
		
	if(msg_if_successful):
		print(msg_if_successful)
	return True
if __name__ == '__main__':

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_socket.bind(('', 8000))

	data_dict = {}
	plugs = {}
	
	plugs["dehumidifier"] = SmartPlug(DEHUMIDIFIER_IP)
	plugs["fridge"] = SmartPlug(FRIDGE_IP)
	plugs["humidifier"] = SmartPlug(HUMIDIFIER_IP)

	#last time compressor was seen as on
	compressor_last_on = datetime.datetime.now()
	
	#last time the dehumidifier or humidifier changed state (on/off)
	humidifiers_last_changed = datetime.datetime.now()

	cur = create_db_and_data_table()
	while True:
		try:
			data_dict = receive_data()
			insert_records(data_dict, plugs)
			
			print(f"Humidifier Plug: {plugs['humidifier'].state} | Dehumidifier Plug: {plugs['dehumidifier'].state} | Fridge Plug: {plugs['fridge'].state}")
			print(f"Compressor Last On: {compressor_last_on} | Humidifier/Dehumidifier Last Changed: {humidifiers_last_changed}")
			print("---")
			#if humidity and temperature are in the data dict and are not null
			if("Humidity" in data_dict.keys() and "Temperature(F)" in data_dict.keys() and data_dict["Humidity"] != "na" and data_dict["Temperature(F)"] != "na"):
				humidity = float(data_dict["Humidity"])
				humidity_within_bounds = MIN_HUMIDITY < humidity and humidity < MAX_HUMIDITY
				temperature = float(data_dict["Temperature(F)"])
				temp_within_bounds = MIN_TEMP < temperature and temperature < MAX_TEMP
				
				#keep compressor_last_on updated even if in temp range
				if(plugs["fridge"].state == "ON"):
					compressor_last_on = datetime.datetime.now()
					
				if(not temp_within_bounds):
					#if the temp isn't range, cut power to both humidifier and dehumidifier
					change_plug(plugs["dehumidifier"], "off", "temp not in range: dehumidifier plug turned off")
					change_plug(plugs["humidifier"], "off", "temp not in range: humidifier plug turned off")
					
					###
					# FRIDGE LOGIC
					###
					
					#fridge state logic
					if(temperature > MAX_TEMP):
						change_plug(plugs["fridge"], "on", "fridge plug turned on")
					elif(temperature < MIN_TEMP):
						change_plug(plugs["fridge"], "off", "fridge plug turned off")
				elif(datetime.datetime.now() > (compressor_last_on + datetime.timedelta(minutes=COMPRESSOR_INTERVAL)) 
					and datetime.datetime.now() > (humidifiers_last_changed + datetime.timedelta(minutes=HUMIDITY_INTERVAL
					))):
					#only run humidity ON logic if temp is in range AND the compressor has been off for 10 minutes
					#if humidity too high, pop dehu on
					#must specify state to 
					if(humidity > MAX_HUMIDITY):
						if(change_plug(plugs["dehumidifier"], "on", "dehumidifier plug turned on")):
							humidifiers_last_changed = datetime.datetime.now();
					#if the humidity is too low, turn dehu off
					elif(humidity <= MIN_HUMIDITY):
						if(change_plug(plugs["humidifier"], "on", "humidifier plug turned on")):
							humidifiers_last_changed = datetime.datetime.now();
				
				#run humidity OFF logic any time
				if(humidity < MIN_HUMIDITY):
					if(change_plug(plugs["dehumidifier"], "off", "dehumidifier plug turned off")):
						humidifiers_last_changed = datetime.datetime.now();
					
				if(humidity > MIN_HUMIDITY):
					if(change_plug(plugs["humidifier"], "off", "humidifier plug turned off")):
						humidifiers_last_changed = datetime.datetime.now();
		except KeyboardInterrupt:
			quit()
		except:
			print(f"OPERATION FAILED!! - {datetime.datetime.now()}")
			traceback.print_exc()
