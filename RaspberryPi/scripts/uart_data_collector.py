#!/usr/bin/env python3
"""
UART Data Collection Service for Raspberry Pi
- Receives sensor data from ESP32 Master via UART (Serial Port)
- Saves all 3 nodes (master, node1, node2) data to a unified CSV format
- Captures camera images with LED on every cycle
- Runs as a background service

Wiring:
- ESP32 GPIO17 (TX2) → Pi Pin 10 (GPIO15/RXD)
- ESP32 GPIO16 (RX2) → Pi Pin 8 (GPIO14/TXD)
- ESP32 GND → Pi GND
"""

import serial
import json
import csv
import os
from datetime import datetime
from pathlib import Path
import time
import threading
import logging
from picamera2 import Picamera2
try:
    import lgpio as GPIO
    GPIO_CHIP = 4  # Pi 5 uses chip 4
    USE_LGPIO = True
except ImportError:
    import RPi.GPIO as GPIO
    USE_LGPIO = False

# ==================== Configuration ====================
SERIAL_PORT = "/dev/ttyAMA0"  # Raspberry Pi UART (GPIO14/15)
BAUD_RATE = 115200

# Timing
CAMERA_INTERVAL_SECONDS = 60 * 60  # 60 minutes

# GPIO Configuration
LED_PIN = 17  # GPIO17 (BCM numbering)
gpio_handle = None  # Global handle for lgpio

# Data directories
BASE_DIR = Path.home() / "thesis_data"
DATA_DIR = BASE_DIR / "sensor_data"
IMAGE_DIR = BASE_DIR / "images"

# Logging
LOG_FILE = BASE_DIR / "uart_data_collector.log"

# CSV file path (unified format)
CSV_FILENAME = "unified_sensor_data.csv"

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
    global gpio_handle
    try:
        if USE_LGPIO:
            # Pi 5 using lgpio (INVERTED LOGIC: 1=OFF, 0=ON)
            gpio_handle = GPIO.gpiochip_open(GPIO_CHIP)
            GPIO.gpio_claim_output(gpio_handle, LED_PIN, 1)  # Start with 1 = OFF
            logger.info(f"GPIO {LED_PIN} configured for LED (using lgpio - inverted logic)")
        else:
            # Older Pi using RPi.GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(LED_PIN, GPIO.OUT)
            GPIO.output(LED_PIN, GPIO.LOW)
            logger.info(f"GPIO {LED_PIN} configured for LED (using RPi.GPIO)")
        
        # Ensure LED is OFF at startup
        led_off()
        logger.info("LED initialized to OFF state")
    except Exception as e:
        logger.warning(f"GPIO setup failed: {e}. LED control disabled.")
        gpio_handle = None

def led_on():
    """Turn LED on"""
    try:
        if USE_LGPIO and gpio_handle is not None:
            # INVERTED LOGIC: 0 = ON
            GPIO.gpio_write(gpio_handle, LED_PIN, 0)
        elif not USE_LGPIO:
            GPIO.output(LED_PIN, GPIO.HIGH)
    except Exception as e:
        logger.warning(f"LED control failed: {e}")

def led_off():
    """Turn LED off"""
    try:
        if USE_LGPIO and gpio_handle is not None:
            # INVERTED LOGIC: 1 = OFF
            GPIO.gpio_write(gpio_handle, LED_PIN, 1)
        elif not USE_LGPIO:
            GPIO.output(LED_PIN, GPIO.LOW)
    except Exception as e:
        logger.warning(f"LED control failed: {e}")

# ==================== Camera Functions ====================
class CameraController:
    def __init__(self):
        self.picam2 = None
        self.initialized = False
        
    def initialize(self):
        """Initialize camera with autofocus"""
        try:
            if not self.initialized:
                self.picam2 = Picamera2()
                config = self.picam2.create_still_configuration()
                self.picam2.configure(config)
                
                # Set autofocus mode to continuous
                self.picam2.set_controls({"AfMode": 2})  # 2 = Continuous autofocus
                
                self.picam2.start()
                time.sleep(2)  # Warm up
                self.initialized = True
                logger.info("Camera initialized successfully with continuous autofocus")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.initialized = False
    
    def capture_with_led(self):
        """Capture image with LED on and autofocus"""
        try:
            if not self.initialized:
                self.initialize()
            
            # Turn LED on
            led_on()
            logger.info("LED ON")
            
            # Trigger autofocus and wait for it to complete
            try:
                self.picam2.set_controls({"AfTrigger": 0})
                logger.info("Autofocus triggered")
            except Exception as af_err:
                logger.warning(f"Autofocus trigger failed: {af_err}")
            
            time.sleep(3)  # Wait for autofocus to complete and LED to stabilize
            
            # Check focus status
            try:
                metadata = self.picam2.capture_metadata()
                if 'AfState' in metadata:
                    af_states = {0: "Idle", 1: "Scanning", 2: "Focused", 3: "Failed"}
                    logger.info(f"Autofocus state: {af_states.get(metadata['AfState'], 'Unknown')}")
                if 'LensPosition' in metadata:
                    logger.info(f"Lens position: {metadata['LensPosition']:.2f}")
            except Exception as meta_err:
                logger.warning(f"Could not read AF metadata: {meta_err}")
            
            # Capture image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = IMAGE_DIR / f"capture_{timestamp}.jpg"
            
            self.picam2.capture_file(str(filename))
            
            # Turn LED off immediately after capture
            led_off()
            logger.info("LED OFF - Capture complete")
            
            file_size = filename.stat().st_size / 1024  # KB
            logger.info(f"Captured image: {filename.name} ({file_size:.2f} KB)")
            
            return True
            
        except Exception as e:
            led_off()  # Make sure LED is off on error
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

# ==================== Data Saving (Unified CSV Format) ====================
def save_unified_data(data):
    """Save unified sensor data from all 3 nodes to a single CSV"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_file = DATA_DIR / CSV_FILENAME
        
        # Check if file exists to determine if we need headers
        file_exists = csv_file.exists()
        
        # Extract data from JSON
        cycle = data.get('cycle', 'N/A')
        
        master = data.get('master', {})
        node1 = data.get('node1', {})
        node2 = data.get('node2', {})
        
        # Prepare row with unified format
        row = {
            'timestamp': timestamp,
            'cycle_number': cycle,
            # Master node data
            'master_temp': master.get('temp', 'N/A') if master.get('received') else 'N/A',
            'master_hum': master.get('hum', 'N/A') if master.get('received') else 'N/A',
            'master_tvoc': master.get('tvoc', 'N/A') if master.get('received') else 'N/A',
            'master_eco2': master.get('eco2', 'N/A') if master.get('received') else 'N/A',
            'master_mq3_ppm': master.get('mq3_ppm', 'N/A') if master.get('received') else 'N/A',
            # Node1 data
            'node1_temp': node1.get('temp', 'N/A') if node1.get('received') else 'N/A',
            'node1_hum': node1.get('hum', 'N/A') if node1.get('received') else 'N/A',
            'node1_tvoc': node1.get('tvoc', 'N/A') if node1.get('received') else 'N/A',
            'node1_eco2': node1.get('eco2', 'N/A') if node1.get('received') else 'N/A',
            'node1_mq3_ppm': node1.get('mq3_ppm', 'N/A') if node1.get('received') else 'N/A',
            # Node2 data
            'node2_temp': node2.get('temp', 'N/A') if node2.get('received') else 'N/A',
            'node2_hum': node2.get('hum', 'N/A') if node2.get('received') else 'N/A',
            'node2_tvoc': node2.get('tvoc', 'N/A') if node2.get('received') else 'N/A',
            'node2_eco2': node2.get('eco2', 'N/A') if node2.get('received') else 'N/A',
            'node2_mq3_ppm': node2.get('mq3_ppm', 'N/A') if node2.get('received') else 'N/A',
        }
        
        fieldnames = [
            'timestamp', 'cycle_number',
            'master_temp', 'master_hum', 'master_tvoc', 'master_eco2', 'master_mq3_ppm',
            'node1_temp', 'node1_hum', 'node1_tvoc', 'node1_eco2', 'node1_mq3_ppm',
            'node2_temp', 'node2_hum', 'node2_tvoc', 'node2_eco2', 'node2_mq3_ppm'
        ]
        
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                logger.info(f"Created new CSV file: {CSV_FILENAME}")
            
            writer.writerow(row)
        
        logger.info(f"✓ Cycle {cycle}: Saved unified data - Master={master.get('received')}, Node1={node1.get('received')}, Node2={node2.get('received')}")
        
        # Log key values for monitoring
        if master.get('received'):
            logger.info(f"  Master: T={master.get('temp')}°C, TVOC={master.get('tvoc')}, MQ3={master.get('mq3_ppm')}")
        
    except Exception as e:
        logger.error(f"Failed to save unified data: {e}")

# ==================== UART Reading ====================
def read_uart_data(ser):
    """Read and process data from UART"""
    logger.info("Starting UART data collection...")
    
    while True:
        try:
            if ser.in_waiting > 0:
                # Read line from UART
                line = ser.readline().decode('utf-8').strip()
                
                if not line:
                    continue
                
                logger.debug(f"Received: {line[:100]}...")  # Log first 100 chars
                
                try:
                    # Parse JSON data
                    data = json.loads(line)
                    
                    # Validate data structure
                    if 'master' in data and 'node1' in data and 'node2' in data:
                        save_unified_data(data)
                    else:
                        logger.warning(f"Invalid data structure received: {list(data.keys())}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.debug(f"Raw data: {line}")
                    
        except Exception as e:
            logger.error(f"Error reading UART: {e}")
            time.sleep(1)

# ==================== Camera Timer Thread ====================
def camera_timer_thread():
    """Independent thread that captures images every 30 minutes"""
    logger.info(f"Camera timer started - capturing every {CAMERA_INTERVAL_SECONDS}s")
    logger.info(f"First capture will occur in {CAMERA_INTERVAL_SECONDS}s")
    
    while True:
        try:
            # Wait FIRST, then capture (don't capture on startup)
            time.sleep(CAMERA_INTERVAL_SECONDS)
            camera.capture_with_led()
        except Exception as e:
            logger.error(f"Camera timer error: {e}")
            time.sleep(60)  # Wait 1 minute before retry

# ==================== Main ====================
def main():
    """Main application loop"""
    logger.info("=" * 60)
    logger.info("  Thesis UART Data Collection Service Starting")
    logger.info("=" * 60)
    
    # Setup
    setup_directories()
    setup_gpio()
    camera.initialize()
    
    # Start camera timer thread
    camera_thread = threading.Thread(target=camera_timer_thread, daemon=True)
    camera_thread.start()
    logger.info("Camera timer thread started")
    
    # Setup serial connection
    try:
        logger.info(f"Opening serial port {SERIAL_PORT} at {BAUD_RATE} baud...")
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        logger.info(f"✓ Serial port opened successfully")
        logger.info(f"Waiting for data from ESP32...")
        
        # Start reading UART data
        read_uart_data(ser)
        
    except serial.SerialException as e:
        logger.error(f"Failed to open serial port: {e}")
        logger.error("Make sure:")
        logger.error(f"  1. Serial console is disabled on {SERIAL_PORT}")
        logger.error("  2. ESP32 is connected and powered")
        logger.error("  3. Wiring is correct (ESP32 TX→Pi RX, ESP32 RX→Pi TX, GND→GND)")
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        camera.cleanup()
        GPIO.cleanup()
        if 'ser' in locals() and ser.is_open:
            ser.close()
        logger.info("Service stopped")

if __name__ == "__main__":
    main()
