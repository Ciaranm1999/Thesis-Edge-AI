#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include "DHT.h"
#include "Adafruit_SGP30.h"
#include <Preferences.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --------- WiFi & MQTT Configuration ---------
const char* WIFI_SSID = "RaspberryPi_AP";         // <-- Pi's AP SSID
const char* WIFI_PASSWORD = "YOUR_AP_PASSWORD";   // <-- Pi's AP Password
const char* MQTT_BROKER = "192.168.4.1";          // <-- Pi's AP IP (default for hostapd)
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC_MASTER = "sensors/master/data";
const char* MQTT_TOPIC_NODE1 = "sensors/node1/data";
const char* MQTT_TOPIC_NODE2 = "sensors/node2/data";

// --------- General config ---------
const uint32_t CYCLE_SECONDS          = 120;      // total cycle length (active + sleep)
const uint8_t  SGP_WARMUP_SECONDS     = 45;       // SGP30 warmup calls
const uint32_t MASTER_LISTEN_WINDOW_MS = 30000;  // 30 s listen window (increased for better sync)

const bool DEBUG_PRINT_LOCAL_MAC      = false;
const bool DEBUG_PRINT_TIMING         = true;
const bool DEBUG_PRINT_MAC_EVENTS     = true;
const bool DEBUG_NO_SLEEP             = false;

const bool ENABLE_HUMAN_OUTPUT        = true;
const bool ENABLE_CSV_OUTPUT          = false;

// --------- Sensors ---------
#define DHTPIN   4
#define DHTTYPE  DHT22
DHT dht(DHTPIN, DHTTYPE);

Adafruit_SGP30 sgp;

const int MQ3_PIN = 34;

// MQ3 + divider config (same as node)
const float MQ3_VCC        = 5.0f;
const float ADC_REF        = 3.3f;
const float ADC_MAX        = 4095.0f;
const float MQ3_RL         = 1000.0f;

const float DIVIDER_TOP    = 56000.0f;   // 56k between MQ3 and node
const float DIVIDER_BOTTOM = 100000.0f;  // 100k between node and GND
const float DIVIDER_RATIO  = DIVIDER_BOTTOM / (DIVIDER_TOP + DIVIDER_BOTTOM);

// Preferences (NVS) for MQ3 R0
Preferences prefs;
float MQ3_R0 = 20000.0f;
const char* PREFS_NAMESPACE = "mq3";
const char* PREFS_KEY       = "r0";

// --------- Packet format ---------
typedef struct __attribute__((packed)) {
  float    temp;
  float    hum;
  uint16_t tvoc;
  uint16_t eco2;
  float    mq3_ppm;
  uint32_t timestamp;  // millis() at time of reading
} SensorPacket;

// Timing correction packet to send to nodes
typedef struct __attribute__((packed)) {
  int32_t adjustmentMs;  // positive = sleep longer, negative = sleep shorter
} TimingPacket;

SensorPacket masterPkt;
SensorPacket node1Pkt;
SensorPacket node2Pkt;

bool node1ReceivedThisCycle = false;
bool node2ReceivedThisCycle = false;

// Timing tracking
unsigned long node1ArrivalTime = 0;
unsigned long node2ArrivalTime = 0;

// --------- Node MAC addresses ---------
uint8_t node1Mac[] = { 0xE0, 0x8C, 0xFE, 0x2D, 0xD8, 0x60 }; // Node 1 MAC: E0:8C:FE:2D:D8:60
uint8_t node2Mac[] = { 0x7C, 0x9E, 0xBD, 0x45, 0x2A, 0xB4 }; // Node 2 MAC: 7C:9E:BD:45:2A:B4

// --------- WiFi & MQTT Clients ---------
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// --------- Timing ---------
unsigned long startMs      = 0;
unsigned long listenStartMs = 0;

// --------- MQ3 helper ---------
float MQ3_getResistance() {
  int adc = analogRead(MQ3_PIN);

  float v_adc = (adc / ADC_MAX) * ADC_REF;   // voltage at ESP32 ADC pin
  float v_out = v_adc / DIVIDER_RATIO;      // reconstructed MQ3 output voltage

  if (v_out < 0.01f || v_out >= MQ3_VCC) {
    return NAN;
  }

  float v_ratio = (MQ3_VCC - v_out) / v_out;
  float Rs = MQ3_RL * v_ratio;

  return Rs;
}

// --------- Utility functions ---------
bool macEquals(const uint8_t *a, const uint8_t *b) {
  for (int i = 0; i < 6; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}

void printMac(const uint8_t *mac) {
  for (int i = 0; i < 6; i++) {
    if (mac[i] < 16) Serial.print("0");
    Serial.print(mac[i], HEX);
    if (i < 5) Serial.print(":");
  }
}

void printHuman(const char *label, const SensorPacket &p) {
  Serial.print("[");
  Serial.print(label);
  Serial.println("]");
  Serial.print("  Temp: "); Serial.print(p.temp, 2);    Serial.println(" °C");
  Serial.print("  Hum : "); Serial.print(p.hum, 2);     Serial.println(" %RH");
  Serial.print("  TVOC: "); Serial.print(p.tvoc);       Serial.println(" ppb");
  Serial.print("  eCO2: "); Serial.print(p.eco2);       Serial.println(" ppm");
  Serial.print("  MQ3 : "); Serial.print(p.mq3_ppm, 3); Serial.println(" ppm");

  Serial.flush();
}

void printCSV(const char *label, const SensorPacket &p) {
  Serial.print(label); Serial.print(",");
  Serial.print(millis()); Serial.print(",");
  Serial.print(p.temp, 2); Serial.print(",");
  Serial.print(p.hum, 2);  Serial.print(",");
  Serial.print(p.tvoc);    Serial.print(",");
  Serial.print(p.eco2);    Serial.print(",");
  Serial.println(p.mq3_ppm, 3);
}

// --------- Timing Correction Logic ---------
void sendTimingCorrection(const uint8_t *nodeMac, unsigned long arrivalTime) {
  // Calculate how early/late the node arrived
  // Target: nodes should arrive at the start of the listen window (listenStartMs)
  long error = (long)arrivalTime - (long)listenStartMs;
  
  // Simple proportional correction: if node arrived late, tell it to sleep less
  // If node arrived early, tell it to sleep more
  // Negative error = early, positive error = late
  int32_t correction = -error / 2;  // Apply 50% correction to avoid overcorrection
  
  // Limit correction to avoid extreme adjustments
  if (correction > 5000) correction = 5000;    // max 5 seconds faster
  if (correction < -5000) correction = -5000;  // max 5 seconds slower
  
  TimingPacket timingPkt;
  timingPkt.adjustmentMs = correction;
  
  if (DEBUG_PRINT_TIMING) {
    Serial.println("\n----- TIMING CORRECTION -----");
    Serial.print("Node arrival error: ");
    Serial.print(error);
    Serial.println(" ms");
    Serial.print("Sending correction: ");
    Serial.print(correction);
    Serial.print(" ms (");
    if (correction > 0) {
      Serial.print("sleep ");
      Serial.print(correction);
      Serial.println(" ms longer)");
    } else if (correction < 0) {
      Serial.print("sleep ");
      Serial.print(-correction);
      Serial.println(" ms shorter)");
    } else {
      Serial.println("no adjustment)");
    }
    Serial.println("----------------------------\n");
  }
  
  esp_err_t result = esp_now_send(nodeMac, (uint8_t*)&timingPkt, sizeof(TimingPacket));
  if (result != ESP_OK && DEBUG_PRINT_TIMING) {
    Serial.print("[Master] Failed to send timing correction, error: ");
    Serial.println(result);
  }
}

// --------- ESP-NOW callbacks ---------

// Callback signature for ESP32 Arduino core
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  if (DEBUG_PRINT_TIMING) {
    Serial.print("[Master] Timing correction send status: ");
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? "SUCCESS" : "FAILED");
  }
}

// Callback signature for ESP32 Arduino core
void onDataRecv(const uint8_t *mac, const uint8_t *data, int len) {
  if (DEBUG_PRINT_MAC_EVENTS) {
    Serial.print("ESP-NOW packet received from MAC ");
    printMac(mac);
    Serial.print(", len = ");
    Serial.println(len);
  }

  if (len != sizeof(SensorPacket)) {
    if (DEBUG_PRINT_MAC_EVENTS) {
      Serial.println("  -> Unexpected packet size, ignoring.");
    }
    return;
  }

  if (macEquals(mac, node1Mac)) {
    node1ReceivedThisCycle = true;
    node1ArrivalTime = millis();
    memcpy(&node1Pkt, data, sizeof(SensorPacket));

    if (DEBUG_PRINT_TIMING && listenStartMs != 0) {
      unsigned long dt = node1ArrivalTime - listenStartMs;
      float dtSec = dt / 1000.0f;
      Serial.println("\n========== NODE 1 ARRIVAL ==========");
      Serial.print("Time since listen start: ");
      Serial.print(dtSec, 3);
      Serial.println(" s");
      Serial.print("Absolute arrival time: ");
      Serial.print(node1ArrivalTime);
      Serial.println(" ms");
      
      if (node2ReceivedThisCycle) {
        long timeDiff = (long)node1ArrivalTime - (long)node2ArrivalTime;
        Serial.print("Time difference from Node 2: ");
        Serial.print(timeDiff);
        Serial.println(" ms");
      }
      Serial.println("===================================\n");
    }

    if (ENABLE_HUMAN_OUTPUT) printHuman("node1", node1Pkt);
    if (ENABLE_CSV_OUTPUT)   printCSV("node1", node1Pkt);
    
    // Send timing correction to node1
    sendTimingCorrection(node1Mac, node1ArrivalTime);

  } else if (macEquals(mac, node2Mac)) {
    node2ReceivedThisCycle = true;
    node2ArrivalTime = millis();
    memcpy(&node2Pkt, data, sizeof(SensorPacket));

    if (DEBUG_PRINT_TIMING && listenStartMs != 0) {
      unsigned long dt = node2ArrivalTime - listenStartMs;
      float dtSec = dt / 1000.0f;
      Serial.println("\n========== NODE 2 ARRIVAL ==========");
      Serial.print("Time since listen start: ");
      Serial.print(dtSec, 3);
      Serial.println(" s");
      Serial.print("Absolute arrival time: ");
      Serial.print(node2ArrivalTime);
      Serial.println(" ms");
      
      if (node1ReceivedThisCycle) {
        long timeDiff = (long)node2ArrivalTime - (long)node1ArrivalTime;
        Serial.print("Time difference from Node 1: ");
        Serial.print(timeDiff);
        Serial.println(" ms");
      }
      Serial.println("===================================\n");
    }

    if (ENABLE_HUMAN_OUTPUT) printHuman("node2", node2Pkt);
    if (ENABLE_CSV_OUTPUT)   printCSV("node2", node2Pkt);
    
    // Send timing correction to node2
    sendTimingCorrection(node2Mac, node2ArrivalTime);

  } else if (DEBUG_PRINT_MAC_EVENTS) {
    Serial.println("  -> Unknown MAC, ignoring.");
  }
}

// --------- WiFi Connection ---------
void connectWiFi() {
  Serial.print("Connecting to Pi's WiFi AP");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected to Pi's AP");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi connection failed!");
  }
}

// --------- MQTT Connection ---------
void connectMQTT() {
  Serial.print("Connecting to MQTT broker");
  
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 10) {
    if (mqttClient.connect("ESP32_Master")) {
      Serial.println("\n✓ MQTT connected");
      return;
    }
    Serial.print(".");
    delay(500);
    attempts++;
  }
  
  if (!mqttClient.connected()) {
    Serial.println("\n✗ MQTT connection failed!");
  }
}

// --------- Send Data to MQTT ---------
void sendToMQTT(const char* topic, const SensorPacket &pkt) {
  if (!mqttClient.connected()) {
    Serial.println("MQTT not connected, skipping send");
    return;
  }
  
  StaticJsonDocument<256> doc;
  doc["temperature"] = pkt.temp;
  doc["humidity"] = pkt.hum;
  doc["tvoc"] = pkt.tvoc;
  doc["eco2"] = pkt.eco2;
  doc["mq3_ppm"] = pkt.mq3_ppm;
  doc["timestamp"] = millis();
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  if (mqttClient.publish(topic, buffer)) {
    Serial.print("✓ Published to ");
    Serial.println(topic);
  } else {
    Serial.print("✗ Failed to publish to ");
    Serial.println(topic);
  }
}

// --------- ESP-NOW init ---------
void initEspNowMaster() {
  // Initialize WiFi in STA mode for ESP-NOW
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (DEBUG_PRINT_LOCAL_MAC) {
    Serial.print("MASTER WiFi MAC: ");
    Serial.println(WiFi.macAddress());
  }

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed on master!");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);
  esp_now_register_send_cb(onDataSent);

  // Peers for node1 and node2 (not strictly required to receive, but OK)
  esp_now_peer_info_t peerInfo{};
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  // node1
  memcpy(peerInfo.peer_addr, node1Mac, 6);
  esp_now_add_peer(&peerInfo);

  // node2
  memcpy(peerInfo.peer_addr, node2Mac, 6);
  esp_now_add_peer(&peerInfo);
}

// --------- Sleep handling ---------
void goToSleepForRemainingCycle() {
  unsigned long activeMs = millis() - startMs;
  float activeSec = activeMs / 1000.0f;

  long remainingMs = (long)CYCLE_SECONDS * 1000L - (long)activeMs;
  if (remainingMs < 100) remainingMs = 100;

  float remainingSec = remainingMs / 1000.0f;

  if (DEBUG_PRINT_TIMING) {
    Serial.print("Master active time this cycle (s): ");
    Serial.println(activeSec, 3);
    Serial.print("Master going to sleep for (s): ");
    Serial.println(remainingSec, 3);
  }

  if (DEBUG_NO_SLEEP) {
    Serial.println("DEBUG_NO_SLEEP enabled: Master will stay awake and keep listening.");
    while (true) delay(1000);
  } else {
    uint64_t sleepUs = (uint64_t)remainingMs * 1000ULL;
    Serial.println("Master going to deep sleep...");
    esp_sleep_enable_timer_wakeup(sleepUs);
    delay(50);
    esp_deep_sleep_start();
  }
}

// --------- setup / loop ---------
void setup() {
  Serial.begin(115200);
  delay(500);
  startMs = millis();

  Serial.println("MASTER WAKEUP");

  // Load MQ3_R0 from NVS
  prefs.begin(PREFS_NAMESPACE, true); // read-only
  MQ3_R0 = prefs.getFloat(PREFS_KEY, 20000.0f);
  prefs.end();

  Serial.print("Master: loaded MQ3_R0 from NVS (");
  Serial.print(PREFS_NAMESPACE);
  Serial.print("/");
  Serial.print(PREFS_KEY);
  Serial.print(") = ");
  Serial.print(MQ3_R0, 2);
  Serial.println(" ohms");

  // ===== WiFi/MQTT DISABLED FOR ESP-NOW TESTING =====
  // Uncomment below when Raspberry Pi is ready
  /*
// --------- Connect to Pi and send data via MQTT ---------
  Serial.println("\n=== Connecting to Raspberry Pi ===");
  
  // Disconnect ESP-NOW to switch to WiFi STA mode fully
  esp_now_deinit();
  
  // Connect to Pi's WiFi AP
  connectWiFi();
  
  if (WiFi.status() == WL_CONNECTED) {
    // Setup MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    connectMQTT();
    
    if (mqttClient.connected()) {
      // Send master's data
      Serial.println("Sending master data...");
      sendToMQTT(MQTT_TOPIC_MASTER, masterPkt);
      
      // Send node1 data if received
      if (node1ReceivedThisCycle) {
        Serial.println("Sending node1 data...");
        sendToMQTT(MQTT_TOPIC_NODE1, node1Pkt);
      } else {
        Serial.println("⚠ Node1 data not received this cycle");
      }
      
      // Send node2 data if received
      if (node2ReceivedThisCycle) {
        Serial.println("Sending node2 data...");
        sendToMQTT(MQTT_TOPIC_NODE2, node2Pkt);
      } else {
        Serial.println("⚠ Node2 data not received this cycle");
      }
      
      // Allow time for MQTT messages to be sent
      delay(500);
      mqttClient.disconnect();
    }
    
    WiFi.disconnect();
  }
  
  Serial.println("=== Master cycle complete ===\n");
  */

  Serial.println("\n[WiFi/MQTT disabled - ESP-NOW testing mode]\n");
  
  analogReadResolution(12);

  // Init sensors
  dht.begin();
  Wire.begin();

  if (!sgp.begin()) {
    Serial.println("SGP30 init failed on master!");
  }

  initEspNowMaster();

  if (ENABLE_CSV_OUTPUT) {
    Serial.println("label,millis,temp,hum,tvoc,eco2,mq3_ppm");
  }

  // SGP30 warmup
  for (uint8_t i = 0; i < SGP_WARMUP_SECONDS; i++) {
    if (sgp.IAQmeasure()) {
      masterPkt.tvoc = sgp.TVOC;
      masterPkt.eco2 = sgp.eCO2;
    }
    delay(1000);
  }

  // DHT22
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  masterPkt.temp = isnan(t) ? NAN : t;
  masterPkt.hum  = isnan(h) ? NAN : h;

  // MQ3 PPM
  float rs = MQ3_getResistance();
  float ppm = NAN;
  if (!isnan(rs) && rs > 0.0f && MQ3_R0 > 0.0f) {
    float ratio     = rs / MQ3_R0;
    float log_ratio = log10f(ratio);
    ppm = powf(10.0f, ((log_ratio - 0.35f) / -0.47f));
  }
  masterPkt.mq3_ppm = (isnan(ppm) || isinf(ppm)) ? NAN : ppm;

    if (ENABLE_HUMAN_OUTPUT) printHuman("master", masterPkt);
  if (ENABLE_CSV_OUTPUT)   printCSV("master", masterPkt);

  // Listen for node packets
  Serial.println("Master listening for node packets...");
  listenStartMs = millis();

  while (true) {
    unsigned long elapsed = millis() - listenStartMs;

    // Condition 1: both nodes have reported -> stop early
    if (node1ReceivedThisCycle && node2ReceivedThisCycle) {
      Serial.println("Both node1 and node2 packets received, ending listen early.");
      break;
    }

    // Condition 2: listen window expired -> stop
    if (elapsed >= MASTER_LISTEN_WINDOW_MS) {
      Serial.println("Listen window expired, ending listen.");
      break;
    }

    delay(10);  // give ESP-NOW/WiFi time, keep loop light
  }

  // At this point, node1ReceivedThisCycle / node2ReceivedThisCycle
  // tell you which nodes reported this round.
  
  // Small delay to ensure all callback serial output finishes
  delay(100);
  
  // Print summary
  if (DEBUG_PRINT_TIMING) {
    Serial.println("\n============================================");
    Serial.println("   LISTEN WINDOW COMPLETE - SUMMARY");
    Serial.println("============================================");
    
    int count = (node1ReceivedThisCycle ? 1 : 0) + (node2ReceivedThisCycle ? 1 : 0);
    Serial.print("Nodes received: ");
    Serial.print(count);
    Serial.println("/2");
    
    Serial.print("Node 1: ");
    Serial.println(node1ReceivedThisCycle ? "RECEIVED" : "MISSING");
    
    Serial.print("Node 2: ");
    Serial.println(node2ReceivedThisCycle ? "RECEIVED" : "MISSING");
    
    if (node1ReceivedThisCycle && node2ReceivedThisCycle) {
      long timeDiff = abs((long)node1ArrivalTime - (long)node2ArrivalTime);
      Serial.print("Sync offset: ");
      Serial.print(timeDiff);
      Serial.println(" ms");
    }
    
    Serial.println("============================================\n");
  }

  goToSleepForRemainingCycle();
}

void loop() {
  // never used; all work is done in setup() per wake
}
