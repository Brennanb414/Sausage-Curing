#include <DHTesp.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

DHTesp dht;
WiFiUDP Udp;

const IPAddress SENDTO_IP(192,168,10,149);
const int localPort = 8000;
const String WIFI_SSID = "SSID";
const String WIFI_PASS = "Password";
const int RUN_INTERVAL = 5 * 60 * 1000; //5 minutes
float lastSensorOutput[2];

void setup()
{
  Serial.begin(115200);
  
  // set up dht22
  dht.setup(4, DHTesp::DHT22);
  
  //set up wifi
  initWifi();

  //set up UDP
  Udp.begin(localPort);
}

void loop()
{
  runSensor(); 
  char humidity[15];
  char temperature[15];

  dtostrf(lastSensorOutput[0],6,2,humidity);
  dtostrf(lastSensorOutput[1],6,2,temperature);

  unsigned long time = millis();
  char message[75];
  sprintf(message, "Humidity: %s | Temperature(F): %s | Time: %lu", humidity, temperature, time); //time is the current run time since restart - not datetime
  Serial.println(message);
  
  sendUDP(message);
  delay(RUN_INTERVAL);
}

void initWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID,WIFI_PASS);
  Serial.print("Trying to connect to:");
  Serial.print(WIFI_SSID);
  //Serial.print(WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(500);
  }
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());
}

void sendUDP(char *message) {
  Udp.beginPacket(SENDTO_IP, localPort);
  Udp.write(message);
  Udp.endPacket();
}

void runSensor(){
  delay(dht.getMinimumSamplingPeriod());
  lastSensorOutput[0] = dht.getHumidity();
  lastSensorOutput[1] = dht.toFahrenheit(dht.getTemperature());
}