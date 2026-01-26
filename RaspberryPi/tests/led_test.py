#!/usr/bin/env python3
"""
LED Test Script for Raspberry Pi
Tests basic GPIO functionality with LED
"""

import RPi.GPIO as GPIO
import time
import sys

# LED Pin Configuration (BCM numbering)
LED_PIN = 17  # GPIO17 (Physical pin 11)

def setup():
    """Initialize GPIO settings"""
    print("Setting up GPIO...")
    GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
    GPIO.setwarnings(False)
    GPIO.setup(LED_PIN, GPIO.OUT)
    print(f"✓ GPIO {LED_PIN} configured as OUTPUT")

def cleanup():
    """Clean up GPIO settings"""
    GPIO.cleanup()
    print("\n✓ GPIO cleaned up")

def blink_test(times=5, delay=0.5):
    """Blink LED a specified number of times"""
    print(f"\nBlinking LED {times} times...")
    for i in range(times):
        GPIO.output(LED_PIN, GPIO.HIGH)
        print(f"  [{i+1}/{times}] LED ON", end='\r')
        time.sleep(delay)
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"  [{i+1}/{times}] LED OFF", end='\r')
        time.sleep(delay)
    print(f"\n✓ Blink test complete")

def morse_code_test(message="SOS"):
    """Flash LED in Morse code"""
    print(f"\nMorse code - '{message}'")
    
    morse_code = {
        'S': '...',
        'O': '---',
    }
    
    dot_time = 0.2
    dash_time = dot_time * 3
    
    for char in message:
        if char in morse_code:
            pattern = morse_code[char]
            print(f"  {char}: {pattern}")
            for symbol in pattern:
                GPIO.output(LED_PIN, GPIO.HIGH)
                if symbol == '.':
                    time.sleep(dot_time)
                else:
                    time.sleep(dash_time)
                GPIO.output(LED_PIN, GPIO.LOW)
                time.sleep(dot_time)
            time.sleep(dash_time)  # Space between letters
    
    print("✓ Morse code test complete")

def main():
    """Main test sequence"""
    print("=" * 50)
    print("  Raspberry Pi LED Test")
    print("=" * 50)
    print(f"\nUsing GPIO {LED_PIN} (BCM numbering)")
    print("Hardware setup:")
    print("  GPIO17 -> 220Ω Resistor -> LED (+) -> LED (-) -> GND")
    print("")
    
    try:
        setup()
        
        print("\nStarting LED tests...\n")
        
        blink_test(times=5, delay=0.5)
        time.sleep(1)
        
        morse_code_test("SOS")
        
        print("\n" + "=" * 50)
        print("  All tests completed successfully!")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
