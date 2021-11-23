## Components required:
*   tp-link HS100 Smart Plug
*   NodeMCU ESP8266 (ESP-12E)  microcontroller
*   DHT22 Humidity/Temperature Sensor

## Client (NodeMCU):
 (Requires: Arduino IDE setup for ESP8266 chip & DHTesp library)
* Collects data from a DHT22 sensor
* Sends that data through UDP messages to server

## Server:
 (Requires: Python3.x + pyHS100 library)
* Watches for UDP messages from the client, runs logic on those and uses the pyHS100 library to control a connected smart plug
* Stores the data for later analysis in a sqlite db

## Database:
Default name is db.sqlite stored in the Server folder.

To create the proper tables, create your database file then run the following script:
```
CREATE TABLE "DataPoints" (
	"id"	INTEGER NOT NULL,
	"Humidity"	INTEGER,
	"Temperature(F)"	INTEGER,
	"Time"	INTEGER,
	"insert_time"	INTEGER DEFAULT CURRENT_TIMESTAMP,
	"humidifier_state"	TEXT,
	"dehumidifier_state"	TEXT,
	"fridge_state"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
)
```