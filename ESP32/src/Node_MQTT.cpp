#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include "DHT.h"
#include "Adafruit_SGP30.h"
#include <Preferences.h>
#include <ArduinoJson.h>

// --------- WiFi Configuration ---------
const char* WIFI_SSID = "YOUR_WIFI_SSID";      // <-- CHANGE THIS
const char* WIFI_PASSWORD = "YOUR_WIFI_PASS";  // <-- CHANGE THIS

// --------- MQTT Configuration ---------
const char* MQTT_BROKER = "192.168.1.XXX";     // <-- CHANGE TO YOUR PI'S IP
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/node1/data"; // <-- CHANGE FOR EACH NODE

// --------- General config ---------
const uint32_t CYCLE_SECONDS      = 15 * 60;  // 15 minutes
const uint8_t  SGP_WARMUP_SECONDS = 45;       // SGP30 warmup time

const bool NODE_ENABLE_HUMAN_OUTPUT  = true;
const bool NODE_DEBUG_PRINT_TIMING   = true;

// --------- Sensors ---------
#define DHTPIN   4
#define DHTTYPE  DHT22
DHT dht(DHTPIN, DHTTYPE);

Adafruit_SGP30 sgp;

const int MQ3_PIN = 34;

// MQ3 + divider config
const float MQ3_VCC        = 5.0f;
const float ADC_REF        = 3.3f;
const float ADC_MAX        = 4095.0f;
const float MQ3_RL         = 1000.0f;

const float DIVIDER_TOP    = 56000.0f;   // 56k between MQ3 and node
const float DIVIDER_BOTTOM = 100000.0f;  // 100k between node and GND
const float DIVIDER_RATIO  = DIVIDER_BOTTOM / (DIVIDER_TOP + DIVIDER_BOTTOM);

// Preferences (NVS)
Preferences prefs;
float MQ3_R0 = 20000.0f;
const char* PREFS_NAMESPACE = "mq3";
const char* PREFS_KEY       = "r0";

// --------- WiFi & MQTT Clients ---------
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// --------- Sensor Data ---------
struct SensorData {
  float temp;
  float hum;
  uint16_t tvoc;
  uint16_t eco2;
  float mq3_ppm;
} data;

unsigned long startMs = 0;

// --------- MQ3 helpers ---------
float MQ3_getResistance() {
  int adc = analogRead(MQ3_PIN);

  float v_adc = (adc / ADC_MAX) * ADC_REF;
  float v_out = v_adc / DIVIDER_RATIO;

  if (v_out < 0.01f || v_out >= MQ3_VCC) {
    return NAN;
  }

  float v_ratio = (MQ3_VCC - v_out) / v_out;
  float Rs = MQ3_RL * v_ratio;

  return Rs;
}

// --------- WiFi Connection ---------
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi connection failed");
  }
}

// --------- MQTT Connection ---------
bool connectMQTT() {
  Serial.print("Connecting to MQTT broker...");
  
  // Generate unique client ID
  String clientId = "ESP32_Node1_";
  clientId += String(random(0xffff), HEX);
  
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 3) {
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("\n✓ MQTT connected");
      return true;
    } else {
      Serial.print(".");
      attempts++;
      delay(1000);
    }
  }
  
  Serial.println("\n✗ MQTT connection failed");
  return false;
}

// --------- Publish Sensor Data ---------
bool publishData() {
  // Create JSON document
  StaticJsonDocument<256> doc;
  
  doc["temp"] = data.temp;
  doc["hum"] = data.hum;
  doc["tvoc"] = data.tvoc;
  doc["eco2"] = data.eco2;
  doc["mq3_ppm"] = data.mq3_ppm;
  doc["timestamp"] = millis();
  doc["node"] = "node1";
  
  // Serialize to string
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  // Publish
  Serial.print("Publishing to ");
  Serial.print(MQTT_TOPIC);
  Serial.print(": ");
  Serial.println(jsonBuffer);
  
  bool success = mqttClient.publish(MQTT_TOPIC, jsonBuffer, false);
  
  if (success) {
    Serial.println("✓ Data published successfully");
  } else {
    Serial.println("✗ Publish failed");
  }
  
  return success;
}

// --------- Sleep Function ---------
void goToSleepForRemainingCycle() {
  unsigned long activeMs = millis() - startMs;
  long remainingMs = (long)CYCLE_SECONDS * 1000L - (long)activeMs;
  if (remainingMs < 100) remainingMs = 100;

  if (NODE_DEBUG_PRINT_TIMING) {
    Serial.print("Node active time this cycle (ms): ");
    Serial.println(activeMs);
    Serial.print("Node going to sleep for (ms): ");
    Serial.println(remainingMs);
    Serial.print("  (");
    Serial.print(remainingMs / 60000.0);
    Serial.println(" minutes)");
  }

  uint64_t sleepUs = (uint64_t)remainingMs * 1000ULL;
  Serial.println("Node going to deep sleep...");
  
  // Disconnect gracefully
  mqttClient.disconnect();
  WiFi.disconnect(true);
  
  delay(100);
  esp_sleep_enable_timer_wakeup(sleepUs);
  esp_deep_sleep_start();
}

// --------- Setup ---------
void setup() {
  Serial.begin(115200);
  delay(500);
  startMs = millis();

  Serial.println("\n========================================");
  Serial.println("  ESP32 Node MQTT Mode - WAKEUP");
  Serial.println("========================================");

  // Load MQ3_R0 from NVS
  prefs.begin(PREFS_NAMESPACE, true);
  MQ3_R0 = prefs.getFloat(PREFS_KEY, 20000.0f);
  prefs.end();

  Serial.print("Loaded MQ3_R0 = ");
  Serial.print(MQ3_R0, 2);
  Serial.println(" ohms");

  analogReadResolution(12);

  // Init sensors
  Serial.println("\nInitializing sensors...");
  dht.begin();
  Wire.begin();

  if (!sgp.begin()) {
    Serial.println("✗ SGP30 init failed!");
  } else {
    Serial.println("✓ SGP30 initialized");
  }

  // SGP30 warmup
  Serial.print("Warming up SGP30 (");
  Serial.print(SGP_WARMUP_SECONDS);
  Serial.println(" seconds)...");
  
  for (uint8_t i = 0; i < SGP_WARMUP_SECONDS; i++) {
    if (sgp.IAQmeasure()) {
      data.tvoc = sgp.TVOC;
      data.eco2 = sgp.eCO2;
    }
    if (i % 5 == 0) {
      Serial.print(".");
    }
    delay(1000);
  }
  Serial.println(" Done!");

  // Read DHT22
  Serial.println("\nReading DHT22...");
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  data.temp = isnan(t) ? NAN : t;
  data.hum  = isnan(h) ? NAN : h;

  // Read MQ3
  Serial.println("Reading MQ3...");
  float rs = MQ3_getResistance();
  float ppm = NAN;
  if (!isnan(rs) && rs > 0.0f && MQ3_R0 > 0.0f) {
    float ratio     = rs / MQ3_R0;
    float log_ratio = log10f(ratio);
    ppm = powf(10.0f, ((log_ratio - 0.35f) / -0.47f));
  }
  data.mq3_ppm = (isnan(ppm) || isinf(ppm)) ? NAN : ppm;

  // Print readings
  if (NODE_ENABLE_HUMAN_OUTPUT) {
    Serial.println("\n========== Sensor Readings ==========");
    Serial.print("  Temperature: "); Serial.print(data.temp, 2);    Serial.println(" °C");
    Serial.print("  Humidity   : "); Serial.print(data.hum, 2);     Serial.println(" %RH");
    Serial.print("  TVOC       : "); Serial.print(data.tvoc);       Serial.println(" ppb");
    Serial.print("  eCO2       : "); Serial.print(data.eco2);       Serial.println(" ppm");
    Serial.print("  MQ3 Alcohol: "); Serial.print(data.mq3_ppm, 3); Serial.println(" ppm");
    Serial.println("=====================================\n");
  }

  // Connect to WiFi
  connectWiFi();
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot continue without WiFi. Going to sleep...");
    goToSleepForRemainingCycle();
    return;
  }

  // Setup MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  
  // Connect and publish
  if (connectMQTT()) {
    publishData();
    delay(500);  // Give time for publish to complete
  }

  // Go to sleep
  goToSleepForRemainingCycle();
}

void loop() {
  // Never reached - all work done in setup() before deep sleep
}
