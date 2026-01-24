# Raspberry Pi SSH Setup Guide

## Prerequisites
- Raspberry Pi with Raspberry Pi OS installed
- Network connection (WiFi or Ethernet)
- Windows PC with PowerShell

## Step 1: Enable SSH on Raspberry Pi

### Option A: Using Raspberry Pi Desktop (if you have monitor connected)
1. Open **Raspberry Pi Configuration**:
   - Menu → Preferences → Raspberry Pi Configuration
2. Go to **Interfaces** tab
3. Enable **SSH**
4. Click **OK**

### Option B: Headless Setup (no monitor)
1. Insert SD card into your PC
2. Create an empty file named `ssh` (no extension) in the boot partition
3. Safely eject and insert SD card back into Raspberry Pi

## Step 2: Find Your Raspberry Pi's IP Address

### Method 1: Using Router's Admin Page
1. Log into your router (usually `192.168.1.1` or `192.168.0.1`)
2. Look for connected devices list
3. Find device named "raspberrypi" or similar

### Method 2: Using IP Scanner on Windows
```powershell
# Install and use Advanced IP Scanner (free tool)
# Download from: https://www.advanced-ip-scanner.com/
```

### Method 3: If connected to monitor
```bash
# On Raspberry Pi terminal
hostname -I
```

## Step 3: Connect via SSH from Windows

### Using PowerShell (Built-in)
```powershell
# Basic connection
ssh edge@<RASPBERRY_PI_IP>

# Example:
ssh edge@192.168.2.84
```

**Your Credentials:**
- Username: `edge`
- Password: `[your_password]`

### First Time Connection
You'll see a security prompt:
```
The authenticity of host can't be established...
Are you sure you want to continue connecting (yes/no)?
```
Type: `yes`

## Step 4: Change Default Password (IMPORTANT!)
```bash
# After SSH connection
passwd

# Enter current password: raspberry
# Enter new password: [your_secure_password]
# Confirm new password: [your_secure_password]
```

## Step 5: Update Raspberry Pi
```bash
sudo apt update
sudo apt upgrade -y
```

## Step 6: Set Up SSH Key Authentication (Optional but Recommended)

### On Windows PC:
```powershell
# Generate SSH key pair (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to accept default location
# Enter passphrase (or press Enter for no passphrase)

# Copy public key to Raspberry Pi
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@<RASPBERRY_PI_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### Test Key-Based Login:
```powershell
ssh pi@<RASPBERRY_PI_IP>
# Should connect without asking for password
```

## Step 7: Create SSH Config for Easy Access

Create/edit SSH config file:
```powershell
notepad $env:USERPROFILE\.ssh\config
```

Add this content:
```
Host raspi
    HostName <RASPBERRY_PI_IP>
    User pi
    IdentityFile ~/.ssh/id_ed25519
```

Now you can connect with just:
```powershell
ssh raspi
```

## Troubleshooting

### Cannot Connect
1. Check if Raspberry Pi is on the network:
   ```powershell
   ping <RASPBERRY_PI_IP>
   ```

2. Verify SSH is enabled on Pi (if you have monitor access)

3. Check firewall settings on Windows

### Connection Refused
- SSH service might not be running on Pi
- Wrong IP address
- Firewall blocking connection

### Permission Denied
- Wrong username or password
- Check if using correct credentials (default: pi/raspberry)

## Useful SSH Commands

```powershell
# Copy file TO Raspberry Pi
scp file.txt pi@<RASPBERRY_PI_IP>:~/

# Copy file FROM Raspberry Pi
scp pi@<RASPBERRY_PI_IP>:~/file.txt .

# Copy folder recursively
scp -r folder/ pi@<RASPBERRY_PI_IP>:~/

# SSH with port forwarding (useful for VNC or web servers)
ssh -L 5900:localhost:5900 pi@<RASPBERRY_PI_IP>
```

## Next Steps
Once SSH is working, you can:
- Install camera drivers
- Run Python scripts remotely
- Set up development environment
- Configure camera module

---

**Your Raspberry Pi IP:** _________________ (fill this in once found)
