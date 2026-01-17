#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include "DHT.h"
#include "Adafruit_SGP30.h"
#include <Preferences.h>

// --------- General config ---------
const uint32_t CYCLE_SECONDS          = 120;      // total cycle length (active + sleep)
const uint8_t  SGP_WARMUP_SECONDS     = 45;       // SGP30 warmup calls
const uint32_t MASTER_LISTEN_WINDOW_MS = 15000;  // 15 s listen window

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
} SensorPacket;

SensorPacket masterPkt;
SensorPacket node1Pkt;
SensorPacket node2Pkt;

bool node1ReceivedThisCycle = false;
bool node2ReceivedThisCycle = false;

// --------- Node MAC addresses ---------
// !!! REPLACE THESE WITH YOUR ACTUAL NODE MACS !!!
uint8_t node1Mac[] = { 0x7C, 0x9E, 0xBD, 0x45, 0x2A, 0xB4 }; // Node 1 MAC
uint8_t node2Mac[] = { 0xB0, 0xA7, 0x32, 0xDA, 0xAE, 0x58 }; // Node 2 MAC

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

// --------- ESP-NOW callbacks ---------

// New signature for ESP-NOW send callback with ESP-IDF v5 / new core
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
  (void)info; // currently unused
  // Master is not sending anything right now, so we keep this as a stub.
}

// New signature for ESP-NOW receive callback with ESP-IDF v5 / new core
void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  const uint8_t *mac = info->src_addr;

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
    memcpy(&node1Pkt, data, sizeof(SensorPacket));

    if (DEBUG_PRINT_TIMING && listenStartMs != 0) {
      unsigned long dt = millis() - listenStartMs;
      float dtSec = dt / 1000.0f;
      Serial.print("  -> node1 arrived ");
      Serial.print(dtSec, 3);
      Serial.println(" s after listen start");
    }

    if (ENABLE_HUMAN_OUTPUT) printHuman("node1", node1Pkt);
    if (ENABLE_CSV_OUTPUT)   printCSV("node1", node1Pkt);

  } else if (macEquals(mac, node2Mac)) {
    node2ReceivedThisCycle = true;
    memcpy(&node2Pkt, data, sizeof(SensorPacket));

    if (DEBUG_PRINT_TIMING && listenStartMs != 0) {
      unsigned long dt = millis() - listenStartMs;
      float dtSec = dt / 1000.0f;
      Serial.print("  -> node2 arrived ");
      Serial.print(dtSec, 3);
      Serial.println(" s after listen start");
    }

    if (ENABLE_HUMAN_OUTPUT) printHuman("node2", node2Pkt);
    if (ENABLE_CSV_OUTPUT)   printCSV("node2", node2Pkt);

  } else if (DEBUG_PRINT_MAC_EVENTS) {
    Serial.println("  -> Unknown node (MAC does not match node1 or node2)");
  }
}

// --------- ESP-NOW init ---------
void initEspNowMaster() {
  WiFi.mode(WIFI_STA);

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

  goToSleepForRemainingCycle();
}

void loop() {
  // never used; all work is done in setup() per wake
}
