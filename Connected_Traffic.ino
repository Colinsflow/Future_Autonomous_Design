#include "Firebase_Arduino_WiFiNINA.h"
#include <Arduino_JSON.h>
#include <time.h>

#define FIREBASE_HOST "***********"
#define FIREBASE_AUTH "***********"

#define WIFI_SSID "***********"
#define WIFI_PASSWORD "***********"
FirebaseData firebaseData;
//Define Firebase data object
//FirebaseData stream;
long currMillis, prevMillis;
String path = "/Lights/Pattern";
String data = "";
int GREEN = 2;
int YELLOW = 3;
int RED = 4;
int GREEN2 = 5;
int YELLOW2 = 6;
int RED2 = 7;
int current_state = 0;
int Ycnt = 1000;
int Rcnt = 500;
int LED_Status = 0;
char str_north[6] = "north"; // Initialize the first string
char str_east[5] = "east";
char str_south[6] = "south"; // Initialize the first string
char str_west[5] = "west";
char emergency[10] = "Emergency";
String Light_num = "11";
int switch_time = 10000;
int fast_switch_time = 5000;
void setup() {
  pinMode(GREEN, OUTPUT); // set pin 2 as output 
  pinMode(YELLOW, OUTPUT); // set pin 3 as output
  pinMode(RED, OUTPUT); // set pin 4 as output
  pinMode(GREEN2, OUTPUT); // set pin 5 as output
  pinMode(YELLOW2, OUTPUT); // set pin 6 as output
  pinMode(RED2, OUTPUT); // set pin 7 as output
  Serial.begin(9600);
  delay(100);
  Serial.println();

  Serial.print("Connecting to Wi-Fi");
  int status = WL_IDLE_STATUS;
  while (status != WL_CONNECTED) {
    status = WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print(".");
    delay(100);
  }
  Serial.println();
  Serial.print("Connected with IP: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  //Provide the autntication data
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH, WIFI_SSID, WIFI_PASSWORD);
  Firebase.reconnectWiFi(true);
}

void loop() {
  if(Firebase.getString(firebaseData, "/Lights/Pattern")) {
    data = firebaseData.stringData();
  }
  if (data == "Normal") {
    digitalWrite(RED2, HIGH);
    digitalWrite(RED, LOW);
    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, LOW);
    digitalWrite(GREEN, LOW);
    digitalWrite(YELLOW, HIGH);
    delay(Ycnt); //switch to yellow lights
    digitalWrite(YELLOW, LOW);
    digitalWrite(RED, HIGH);
    delay(Rcnt); //time where both lights are red
    digitalWrite(GREEN2, HIGH);
    digitalWrite(RED2, LOW);   
    Firebase.setString(firebaseData, "/Lights/"+ Light_num , str_south);
    delay(switch_time);
    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, HIGH);
    delay(Ycnt); //switch to yellow lights
    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED2, HIGH);
    delay(Rcnt); //time where both lights are red
    
    digitalWrite(GREEN, HIGH);
    digitalWrite(RED, LOW);
    Firebase.setString(firebaseData, "/Lights/"+ Light_num, str_west);
    delay(switch_time);      
  }
  if (data == "Fast") {
    digitalWrite(RED2, HIGH);
    digitalWrite(RED, LOW);
    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, LOW);
    digitalWrite(GREEN, LOW);
    digitalWrite(YELLOW, HIGH);
    delay(Ycnt); //switch to yellow lights
    digitalWrite(YELLOW, LOW);
    digitalWrite(RED, HIGH);
    delay(Rcnt); //time where both lights are red
      
    digitalWrite(GREEN2, HIGH);
    digitalWrite(RED2, LOW);   
    Firebase.setString(firebaseData, "/Lights/"+ Light_num, str_south);
  
    delay(fast_switch_time);
    
    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, HIGH);
    delay(Ycnt); //switch to yellow lights
    
    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED2, HIGH);
    delay(Rcnt); //time where both lights are red
    
    digitalWrite(GREEN, HIGH);
    digitalWrite(RED, LOW);
    Firebase.setString(firebaseData, "/Lights/"+ Light_num, str_west);
    delay(fast_switch_time);

  }
  if (data == "Emergency") {
    digitalWrite(GREEN2, LOW);
    digitalWrite(GREEN, LOW);
    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED, LOW);
    digitalWrite(YELLOW, HIGH);
    digitalWrite(RED2, HIGH);

    Firebase.setString(firebaseData, "/Lights/"+ Light_num , emergency);
  
    delay(500);
    digitalWrite(YELLOW, LOW);
    digitalWrite(RED2, LOW);
    digitalWrite(RED, HIGH);
    digitalWrite(YELLOW2, HIGH);
    Firebase.setString(firebaseData, "/Lights/"+ Light_num , emergency);
    delay(500);
  }
  
}




