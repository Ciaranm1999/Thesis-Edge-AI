#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_SGP30.h"
#include "DHT.h"
#include <Preferences.h>   // Non-volatile storage

/* ===================== PINS ===================== */
#define DHTPIN   4          // DHT22 data pin
#define DHTTYPE  DHT22
#define SDA_PIN  21         // I2C SDA
#define SCL_PIN  22         // I2C SCL
#define MQ3_PIN  34         // MQ3 analog pin (ESP32 ADC)

/* ===================== TIMING ===================== */
#define DHT_INTERVAL 2000
#define SGP_INTERVAL 1000

/* ===================== MQ3 CONFIG ===================== */
// Flying Fish board typical 10k load resistor:
#define MQ3_RL 1000.0

// Divider: 56k (top) / 100k (bottom)
static const float DIVIDER_RATIO = 0.641f; // ESP32 sees ~64% of true signal

// Default fallback R0
static const float R0_FALLBACK = 12000.0f;

/* ===================== GLOBALS ===================== */
DHT dht(DHTPIN, DHTTYPE);
Adafruit_SGP30 sgp;
Preferences prefs;

unsigned long lastDhtTime = 0;
unsigned long lastSgpTime = 0;
float lastTemp = NAN;
float lastHum  = NAN;

float MQ3_R0 = R0_FALLBACK;

/* ===================== HELPERS ===================== */

// Compute absolute humidity (g/m³)
float computeAbsoluteHumidity(float temperature, float humidity) {
  float svp = 6.112f * expf((17.62f * temperature) / (243.12f + temperature));
  float avp = humidity / 100.0f * svp;
  return 216.7f * (avp / (temperature + 273.15f));
}

// Compute MQ3 sensor resistance
float MQ3_getResistance() {
  int adc = analogRead(MQ3_PIN);
  float v_adc = (adc / 4095.0f) * 3.3f;     // voltage at ESP32 ADC
  float v_out = v_adc / DIVIDER_RATIO;      // reconstruct 5V-side voltage
  if (v_out < 0.01f) v_out = 0.01f;
  float v_ratio = (5.0f - v_out) / v_out;
  return MQ3_RL * v_ratio;                  // Rs = RL * (Vc - Vout)/Vout
}

// Save a new R0 value to NVS
void saveR0toNVS(float newR0) {
  prefs.putFloat("r0", newR0);
  MQ3_R0 = newR0;
  Serial.print("Saved new R0 to NVS: ");
  Serial.print(MQ3_R0, 2);
  Serial.println(" ohms");
}

/* ===================== SETUP ===================== */
void setup() {
  Serial.begin(115200);
  delay(1000); // give Serial time to connect

  // Load R0 from NVS
  prefs.begin("mq3", false);
  if (prefs.isKey("r0")) {
    MQ3_R0 = prefs.getFloat("r0", R0_FALLBACK);
    Serial.print("Loaded MQ3 R0 from NVS: ");
    Serial.print(MQ3_R0, 2);
    Serial.println(" ohms");
  } else {
    MQ3_R0 = R0_FALLBACK;
    Serial.print("No stored R0 found. Using fallback: ");
    Serial.print(MQ3_R0, 2);
    Serial.println(" ohms");
  }

  // Sensor inits
  dht.begin();
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  if (!sgp.begin(&Wire)) {
    Serial.println("ERROR: SGP30 not found. Check wiring!");
    while (1) delay(100);
  }
  Serial.println("SGP30 initialized. (Allow 15–30 s warm-up)");

  analogReadResolution(12);
  Serial.println("Type 'R0?' to query or 'R0=xxxxx' to update stored R0.\n");
}

/* ===================== LOOP ===================== */
void loop() {
  unsigned long now = millis();

  // --- Serial command interface ---
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.equalsIgnoreCase("R0?")) {
      Serial.print("Current R0 = ");
      Serial.print(MQ3_R0, 2);
      Serial.println(" ohms");
    } 
    else if (cmd.startsWith("R0=")) {
      String valStr = cmd.substring(3);
      float newR0 = valStr.toFloat();
      if (newR0 > 1000 && newR0 < 1000000) {  // sanity bounds
        saveR0toNVS(newR0);
      } else {
        Serial.println("Invalid R0 value (out of range).");
      }
    } 
    else {
      Serial.println("Unknown command. Use R0? or R0=xxxxx");
    }
  }

  // --- DHT22 reading ---
  if (now - lastDhtTime >= DHT_INTERVAL) {
    lastDhtTime = now;
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      lastTemp = t;
      lastHum  = h;
      Serial.print("DHT22 -> ");
      Serial.print(t, 1); Serial.print(" °C, ");
      Serial.print(h, 1); Serial.println(" % RH");
    } else {
      Serial.println("DHT22 read failed.");
    }
  }

  // --- SGP30 reading ---
  if (now - lastSgpTime >= SGP_INTERVAL) {
    lastSgpTime = now;

    if (!isnan(lastTemp) && !isnan(lastHum)) {
      float absHum = computeAbsoluteHumidity(lastTemp, lastHum);
      sgp.setHumidity(absHum);
    }

    if (sgp.IAQmeasure()) {
      Serial.print("SGP30 -> eCO2: ");
      Serial.print(sgp.eCO2);
      Serial.print(" ppm, TVOC: ");
      Serial.print(sgp.TVOC);
      Serial.println(" ppb");
    } else {
      Serial.println("SGP30 measurement failed!");
    }

    if (sgp.IAQmeasureRaw()) {
      Serial.print("Raw H2: "); Serial.print(sgp.rawH2);
      Serial.print(", Raw Ethanol: "); Serial.println(sgp.rawEthanol);
    }

    // --- MQ3 reading ---
    float rs = MQ3_getResistance();
    float ratio = rs / MQ3_R0;
    float ppm = pow(10.0f, ((log10f(ratio) - 0.35f) / -0.47f));

    Serial.print("MQ3 -> Rs/R0 ratio: ");
    if (isnan(ratio) || isinf(ratio)) Serial.print("n/a");
    else Serial.print(ratio, 2);
    Serial.print(", Approx Alcohol PPM: ");
    if (isnan(ppm) || isinf(ppm)) Serial.println("n/a");
    else Serial.println(ppm, 1);

    Serial.println("--------------------------------");
  }
}
