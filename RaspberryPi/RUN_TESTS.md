# Commands to Run - Copy and Paste Guide

## PART 1: Upload Scripts (Run in NEW Windows PowerShell)

Open a NEW PowerShell window (not the SSH one) and run:

```powershell
cd "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Block 3\Smart Systems Project\Thesis-Edge-AI\RaspberryPi"

scp camera_test.sh camera_test.py led_test.py edge@192.168.2.84:~/
```

Enter your password when prompted.

---

## PART 2: Test Camera (Run in SSH terminal - where you're connected)

```bash
# Make script executable
chmod +x ~/camera_test.sh

# Run camera test
~/camera_test.sh
```

Photos will be saved to: `~/camera_tests/`

---

## PART 3: Test LED Relay (Run in SSH terminal)

```bash
# Run LED relay test
python3 ~/led_test.py
```

The LED should turn on/off through the relay on GPIO17.

---

## PART 4: Download Photos to Windows PC

After camera tests, download the photos (run in Windows PowerShell):

```powershell
# Create local directory
mkdir camera_images -ErrorAction SilentlyContinue

# Download all photos
scp edge@192.168.2.84:~/camera_tests/*.jpg .\camera_images\
scp edge@192.168.2.84:~/camera_tests/*.h264 .\camera_images\
```

Photos will be in: `.\camera_images\`

---

## Quick Commands Summary

**Windows PowerShell:**
```powershell
# 1. Upload scripts
cd "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Block 3\Smart Systems Project\Thesis-Edge-AI\RaspberryPi"
scp camera_test.sh camera_test.py led_test.py edge@192.168.2.84:~/

# 2. Download photos later
mkdir camera_images -ErrorAction SilentlyContinue
scp edge@192.168.2.84:~/camera_tests/* .\camera_images\
```

**Raspberry Pi SSH:**
```bash
# 1. Make executable
chmod +x ~/camera_test.sh

# 2. Test camera
~/camera_test.sh

# 3. Test LED relay  
python3 ~/led_test.py

# 4. View saved photos list
ls -lh ~/camera_tests/
```
