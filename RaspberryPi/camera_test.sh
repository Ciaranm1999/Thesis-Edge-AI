#!/bin/bash
# Camera Module 3 Test Script for Raspberry Pi

echo "======================================"
echo "  Camera Module 3 Test Script"
echo "======================================"
echo ""

# Check if camera is detected
echo "Step 1: Checking for camera..."
if libcamera-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
    echo "✓ Camera detected!"
    echo ""
    libcamera-hello --list-cameras
else
    echo "✗ Camera not detected!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check ribbon cable connection"
    echo "2. Enable camera: sudo raspi-config -> Interface Options -> Camera"
    echo "3. Reboot: sudo reboot"
    exit 1
fi

echo ""
echo "Step 2: Testing camera preview (5 seconds)..."
echo "A preview window should appear..."
libcamera-hello -t 5000

echo ""
echo "Step 3: Capturing test image..."
mkdir -p ~/camera_tests
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
libcamera-still -o ~/camera_tests/test_${TIMESTAMP}.jpg

if [ -f ~/camera_tests/test_${TIMESTAMP}.jpg ]; then
    echo "✓ Image captured: ~/camera_tests/test_${TIMESTAMP}.jpg"
    ls -lh ~/camera_tests/test_${TIMESTAMP}.jpg
else
    echo "✗ Failed to capture image"
    exit 1
fi

echo ""
echo "Step 4: Testing video capture (5 seconds)..."
libcamera-vid -t 5000 -o ~/camera_tests/test_${TIMESTAMP}.h264

if [ -f ~/camera_tests/test_${TIMESTAMP}.h264 ]; then
    echo "✓ Video captured: ~/camera_tests/test_${TIMESTAMP}.h264"
    ls -lh ~/camera_tests/test_${TIMESTAMP}.h264
else
    echo "✗ Failed to capture video"
    exit 1
fi

echo ""
echo "======================================"
echo "  Camera Module 3 Test Complete!"
echo "======================================"
echo ""
echo "All test files saved in: ~/camera_tests/"
echo ""
echo "Next steps:"
echo "- View images: scp edge@192.168.2.84:~/camera_tests/*.jpg ."
echo "- Test with Python: python3 camera_test.py"
