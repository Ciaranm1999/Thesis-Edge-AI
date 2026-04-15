#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include "DHT.h"
#include "Adafruit_SGP30.h"
#include <Preferences.h>

// --------- General config ---------
const uint32_t CYCLE_SECONDS      = 120;  // total cycle length (active + sleep)
const uint8_t  SGP_WARMUP_SECONDS = 45;   // SGP30 IAQmeasure() calls during warmup

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
float MQ3_R0 = 20000.0f;   // default fallback if not found
const char* PREFS_NAMESPACE = "mq3";
const char* PREFS_KEY       = "r0";

// --------- ESP-NOW / MAC ---------
uint8_t masterMac[] = {0xCC, 0xDB, 0xA7, 0x98, 0xD2, 0xD0}; // <--- put your master MAC here

typedef struct __attribute__((packed)) {
  float    temp;
  float    hum;
  uint16_t tvoc;
  uint16_t eco2;
  float    mq3_ppm;
} SensorPacket;

SensorPacket pkt;

unsigned long startMs = 0;

// --------- MQ3 helpers ---------
float MQ3_getResistance() {
  int adc = analogRead(MQ3_PIN);

  float v_adc = (adc / ADC_MAX) * ADC_REF;   // voltage at ESP32 ADC pin (0–3.3 V)
  float v_out = v_adc / DIVIDER_RATIO;      // reconstructed MQ3 output voltage (0–5 V)

  if (v_out < 0.01f || v_out >= MQ3_VCC) {
    return NAN;
  }

  float v_ratio = (MQ3_VCC - v_out) / v_out;
  float Rs = MQ3_RL * v_ratio;

  return Rs;
}

// ESP-NOW send callback (optional debug) - NEW SIGNATURE
void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
  // 'info' contains metadata (src/dst MAC, etc.) if you ever need it
  /*
  Serial.print("Last Packet Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
  */
}

void goToSleepForRemainingCycle() {
  unsigned long activeMs = millis() - startMs;
  long remainingMs = (long)CYCLE_SECONDS * 1000L - (long)activeMs;
  if (remainingMs < 100) remainingMs = 100;

  if (NODE_DEBUG_PRINT_TIMING) {
    Serial.print("Node active time this cycle (ms): ");
    Serial.println(activeMs);
    Serial.print("Node going to sleep for (ms): ");
    Serial.println(remainingMs);
  }

  uint64_t sleepUs = (uint64_t)remainingMs * 1000ULL;
  Serial.println("Node going to deep sleep...");
  esp_sleep_enable_timer_wakeup(sleepUs);
  delay(50);
  esp_deep_sleep_start();
}

void setup() {
  Serial.begin(115200);
  delay(500);
  startMs = millis();

  Serial.println("NODE WAKEUP");

  // Load MQ3_R0 from NVS
  prefs.begin(PREFS_NAMESPACE, true);  // read-only
  MQ3_R0 = prefs.getFloat(PREFS_KEY, 20000.0f);
  prefs.end();

  Serial.print("Node: loaded MQ3_R0 from NVS (");
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
    Serial.println("SGP30 init failed on node!");
  }

  // SGP30 warmup
  for (uint8_t i = 0; i < SGP_WARMUP_SECONDS; i++) {
    if (sgp.IAQmeasure()) {
      pkt.tvoc = sgp.TVOC;
      pkt.eco2 = sgp.eCO2;
    }
    delay(1000);
  }

  // DHT22
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  pkt.temp = isnan(t) ? NAN : t;
  pkt.hum  = isnan(h) ? NAN : h;

  // MQ3 PPM
  float rs = MQ3_getResistance();
  float ppm = NAN;
  if (!isnan(rs) && rs > 0.0f && MQ3_R0 > 0.0f) {
    float ratio     = rs / MQ3_R0;
    float log_ratio = log10f(ratio);
    ppm = powf(10.0f, ((log_ratio - 0.35f) / -0.47f));
  }
  pkt.mq3_ppm = (isnan(ppm) || isinf(ppm)) ? NAN : ppm;

  if (NODE_ENABLE_HUMAN_OUTPUT) {
    Serial.println("[node1]");
    Serial.print("  Temp: "); Serial.print(pkt.temp, 2);    Serial.println(" °C");
    Serial.print("  Hum : "); Serial.print(pkt.hum, 2);     Serial.println(" %RH");
    Serial.print("  TVOC: "); Serial.print(pkt.tvoc);       Serial.println(" ppb");
    Serial.print("  eCO2: "); Serial.print(pkt.eco2);       Serial.println(" ppm");
    Serial.print("  MQ3 : "); Serial.print(pkt.mq3_ppm, 3); Serial.println(" ppm");
  }

  // ESP-NOW init & send
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed on node, going to sleep anyway");
    goToSleepForRemainingCycle();
    return;
  }

  esp_now_register_send_cb(onDataSent);

  esp_now_peer_info_t peerInfo{};
  memcpy(peerInfo.peer_addr, masterMac, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add master as peer");
    goToSleepForRemainingCycle();
    return;
  }

  esp_err_t res = esp_now_send(masterMac, (uint8_t*)&pkt, sizeof(SensorPacket));
  if (res != ESP_OK) {
    Serial.print("esp_now_send error: ");
    Serial.println(res);
  } else {
    Serial.println("Node packet sent via ESP-NOW");
  }

  delay(200);  // give radio time to transmit

  goToSleepForRemainingCycle();
}

void loop() {
  // never used; all work done in setup() per wake
}
