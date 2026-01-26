#!/usr/bin/env python3
"""
Data Collection Service for Raspberry Pi
- Subscribes to MQTT topics to receive ESP32 sensor data
- Captures camera images with LED on every 15 minutes (independent of data reception)
- Saves sensor data to CSV files
- Runs as a background service
"""

import paho.mqtt.client as mqtt
import json
import csv
import os
from datetime import datetime
from pathlib import Path
import time
import threading
import logging
from picamera2 import Picamera2
import RPi.GPIO as GPIO

# ==================== Configuration ====================
MQTT_BROKER = "localhost"  # Mosquitto running on Pi
MQTT_PORT = 1883
MQTT_TOPICS = [
    "sensors/master/data",
    "sensors/node1/data",
    "sensors/node2/data"
]

# Timing
CAMERA_INTERVAL_SECONDS = 15 * 60  # 15 minutes

# GPIO Configuration
LED_PIN = 17  # GPIO17 (BCM numbering)

# Data directories
BASE_DIR = Path.home() / "thesis_data"
DATA_DIR = BASE_DIR / "sensor_data"
IMAGE_DIR = BASE_DIR / "images"

# Logging
LOG_FILE = BASE_DIR / "data_collector.log"

# ==================== Setup Logging ====================
def setup_logging():
    """Initialize logging configuration"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== Setup ====================
def setup_directories():
    """Create necessary directories"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Image directory: {IMAGE_DIR}")

def setup_gpio():
    """Initialize GPIO for LED"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LED_PIN, GPIO.OUT)
    GPIO.output(LED_PIN, GPIO.LOW)
    logger.info(f"GPIO {LED_PIN} configured for LED")

# ==================== Camera Functions ====================
class CameraController:
    def __init__(self):
        self.picam2 = None
        self.initialized = False
        
    def initialize(self):
        """Initialize camera"""
        try:
            if not self.initialized:
                self.picam2 = Picamera2()
                config = self.picam2.create_still_configuration()
                self.picam2.configure(config)
                self.picam2.start()
                time.sleep(2)  # Warm up
                self.initialized = True
                logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.initialized = False
    
    def capture_with_led(self):
        """Capture image with LED on"""
        try:
            if not self.initialized:
                self.initialize()
            
            # Turn LED on
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(0.5)  # Let LED stabilize
            
            # Capture image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = IMAGE_DIR / f"capture_{timestamp}.jpg"
            
            self.picam2.capture_file(str(filename))
            
            # Turn LED off
            GPIO.output(LED_PIN, GPIO.LOW)
            
            file_size = filename.stat().st_size / 1024  # KB
            logger.info(f"Captured image: {filename.name} ({file_size:.2f} KB)")
            
            return True
            
        except Exception as e:
            GPIO.output(LED_PIN, GPIO.LOW)  # Make sure LED is off
            logger.error(f"Camera capture failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera resources"""
        try:
            if self.initialized and self.picam2:
                self.picam2.stop()
                self.initialized = False
                logger.info("Camera stopped")
        except Exception as e:
            logger.error(f"Camera cleanup error: {e}")

camera = CameraController()

# ==================== Data Saving ====================
def save_sensor_data(node_name, data):
    """Save sensor data to CSV file"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y%m%d")
        
        # One CSV file per node per day
        csv_file = DATA_DIR / f"{node_name}_{date_str}.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='') as f:
            fieldnames = ['timestamp', 'temperature', 'humidity', 'tvoc', 'eco2', 'mq3_ppm']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            row = {
                'timestamp': timestamp,
                'temperature': data.get('temp', 'N/A'),
                'humidity': data.get('hum', 'N/A'),
                'tvoc': data.get('tvoc', 'N/A'),
                'eco2': data.get('eco2', 'N/A'),
                'mq3_ppm': data.get('mq3_ppm', 'N/A')
            }
            
            writer.writerow(row)
            logger.info(f"Saved data from {node_name}: T={row['temperature']}°C, H={row['humidity']}%, TVOC={row['tvoc']}")
            
    except Exception as e:
        logger.error(f"Failed to save data from {node_name}: {e}")

# ==================== MQTT Callbacks ====================
def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    """Callback when MQTT message received"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.info(f"Received message on {topic}")
        
        # Parse JSON data
        data = json.loads(payload)
        
        # Extract node name from topic (e.g., "sensors/master/data" -> "master")
        node_name = topic.split('/')[1]
        
        # Save data
        save_sensor_data(node_name, data)
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    if rc != 0:
        logger.warning(f"Unexpected MQTT disconnect, return code {rc}")
        logger.info("Attempting to reconnect...")

# ==================== Camera Timer Thread ====================
def camera_timer_thread():
    """Independent thread that captures images every 15 minutes"""
    logger.info(f"Camera timer started - capturing every {CAMERA_INTERVAL_SECONDS}s")
    
    while True:
        try:
            camera.capture_with_led()
            time.sleep(CAMERA_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Camera timer error: {e}")
            time.sleep(60)  # Wait 1 minute before retry

# ==================== Main ====================
def main():
    """Main application loop"""
    logger.info("=" * 60)
    logger.info("  Thesis Data Collection Service Starting")
    logger.info("=" * 60)
    
    # Setup
    setup_directories()
    setup_gpio()
    camera.initialize()
    
    # Start camera timer thread
    camera_thread = threading.Thread(target=camera_timer_thread, daemon=True)
    camera_thread.start()
    logger.info("Camera timer thread started")
    
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to broker
    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start MQTT loop
        logger.info("Starting MQTT loop...")
        client.loop_forever()
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        camera.cleanup()
        GPIO.cleanup()
        client.disconnect()
        logger.info("Service stopped")

if __name__ == "__main__":
    main()
