#!/usr/bin/env python3
"""
Camera Module 3 Python Test with Autofocus
Uses picamera2 library for Camera Module 3
Tests with LED on/off sequence and proper autofocus
Compatible with Raspberry Pi 5 (uses lgpio with INVERTED LOGIC)
"""

from picamera2 import Picamera2
from time import sleep
import os

# GPIO library selection (Pi 5 compatible)
try:
    import lgpio as GPIO
    GPIO_CHIP = 4  # Pi 5 uses chip 4
    USE_LGPIO = True
except ImportError:
    import RPi.GPIO as GPIO
    USE_LGPIO = False

# GPIO Configuration (same as data_collector.py)
LED_PIN = 17  # GPIO17 (BCM numbering)

def test_camera():
    """Test Camera Module 3 functionality with autofocus"""
    print("=" * 50)
    print("  Camera Module 3 - Python Test")
    print("  (with LED control and AUTOFOCUS)")
    print("=" * 50)
    print()
    
    # Setup GPIO
    if USE_LGPIO:
        chip = GPIO.gpiochip_open(GPIO_CHIP)
        GPIO.gpio_claim_output(chip, LED_PIN, 1)  # Start with 1 = OFF (inverted logic)
        print(f"✓ GPIO {LED_PIN} configured for LED (using lgpio - INVERTED LOGIC)")
    else:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"✓ GPIO {LED_PIN} configured for LED (using RPi.GPIO)")
    print()
    
    # Create output directory
    output_dir = os.path.expanduser("~/camera_tests")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Initialize camera
    print("Initializing camera...")
    picam2 = Picamera2()
    
    # Get camera info
    print("\nCamera Information:")
    camera_config = picam2.create_still_configuration()
    print(f"  Resolution: {camera_config['main']['size']}")
    print(f"  Format: {camera_config['main']['format']}")
    
    try:
        # Configure and start camera
        picam2.configure(camera_config)
        
        # Set autofocus mode to continuous
        print("\nSetting autofocus mode...")
        picam2.set_controls({"AfMode": 2})  # 2 = Continuous autofocus
        
        picam2.start()
        print("✓ Camera started with continuous autofocus")
        
        # Warm up
        print("\nWarming up camera (2 seconds)...")
        sleep(2)
        
        # Capture image with LED (matching data_collector.py behavior)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"capture_{timestamp}.jpg")
        
        print(f"\nCapturing image with LED on: {filename}")
        
        # Turn LED on (INVERTED LOGIC for lgpio)
        if USE_LGPIO:
            GPIO.gpio_write(chip, LED_PIN, 0)  # 0 = ON (inverted logic)
        else:
            GPIO.output(LED_PIN, GPIO.HIGH)
        print("✓ LED turned ON")
        
        # Trigger autofocus and wait for it to complete
        print("⚙ Triggering autofocus...")
        picam2.set_controls({"AfTrigger": 0})  # Trigger autofocus
        sleep(3)  # Wait for autofocus to complete and LED to stabilize
        
        # Check focus status
        metadata = picam2.capture_metadata()
        if 'AfState' in metadata:
            af_state = metadata['AfState']
            af_states = {0: "Idle", 1: "Scanning", 2: "Focused", 3: "Failed"}
            print(f"✓ Autofocus state: {af_states.get(af_state, 'Unknown')}")
        
        # Capture image
        print("📸 Capturing image...")
        picam2.capture_file(filename)
        
        # Turn LED off (INVERTED LOGIC for lgpio)
        if USE_LGPIO:
            GPIO.gpio_write(chip, LED_PIN, 1)  # 1 = OFF (inverted logic)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
        print("✓ LED turned OFF")
        
        if os.path.exists(filename):
            file_size = os.path.getsize(filename) / 1024  # KB
            print(f"✓ Image captured successfully!")
            print(f"  File: {filename}")
            print(f"  Size: {file_size:.2f} KB")
        else:
            print("✗ Failed to capture image")
            return False
        
        # Test metadata
        print("\nCamera Metadata:")
        final_metadata = picam2.capture_metadata()
        if 'ExposureTime' in final_metadata:
            print(f"  Exposure Time: {final_metadata['ExposureTime']} µs")
        if 'AnalogueGain' in final_metadata:
            print(f"  Analogue Gain: {final_metadata['AnalogueGain']:.2f}")
        if 'LensPosition' in final_metadata:
            print(f"  Lens Position: {final_metadata['LensPosition']:.2f}")
        if 'AfState' in final_metadata:
            print(f"  AF State: {final_metadata['AfState']}")
        
        print("\n" + "=" * 50)
        print("  Camera test completed successfully!")
        print("=" * 50)
        print(f"\nTo view the image:")
        print(f"  scp edgeai@172.20.10.3:{filename} .")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        # Make sure LED is off
        if USE_LGPIO:
            GPIO.gpio_write(chip, LED_PIN, 1)  # 1 = OFF (inverted logic)
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
        return False
    
    finally:
        picam2.stop()
        # Cleanup GPIO
        if USE_LGPIO:
            GPIO.gpio_free(chip, LED_PIN)
            GPIO.gpiochip_close(chip)
        else:
            GPIO.cleanup()
        print("\n✓ Camera stopped")
        print("✓ GPIO cleaned up")

if __name__ == "__main__":
    test_camera()
