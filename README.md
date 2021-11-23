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
