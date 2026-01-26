#!/usr/bin/env python3
"""
Camera Module 3 Python Test
Uses picamera2 library for Camera Module 3
"""

from picamera2 import Picamera2
from time import sleep
import os

def test_camera():
    """Test Camera Module 3 functionality"""
    print("=" * 50)
    print("  Camera Module 3 - Python Test")
    print("=" * 50)
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
        picam2.start()
        print("\n✓ Camera started")
        
        # Warm up
        print("\nWarming up camera (2 seconds)...")
        sleep(2)
        
        # Capture image
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"capture_{timestamp}.jpg")
        
        print(f"\nCapturing image: {filename}")
        picam2.capture_file(filename)
        
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
        metadata = picam2.capture_metadata()
        if 'ExposureTime' in metadata:
            print(f"  Exposure Time: {metadata['ExposureTime']} µs")
        if 'AnalogueGain' in metadata:
            print(f"  Analogue Gain: {metadata['AnalogueGain']:.2f}")
        
        print("\n" + "=" * 50)
        print("  Camera test completed successfully!")
        print("=" * 50)
        print(f"\nTo view the image:")
        print(f"  scp edge@192.168.2.84:{filename} .")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    finally:
        picam2.stop()
        print("\n✓ Camera stopped")

if __name__ == "__main__":
    test_camera()
