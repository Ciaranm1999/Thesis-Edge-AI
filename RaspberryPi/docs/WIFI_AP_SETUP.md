# Raspberry Pi WiFi Access Point Setup

This guide will help you configure your Raspberry Pi as a WiFi Access Point so the ESP32 Master can connect without requiring your home WiFi network.

## Prerequisites

- Raspberry Pi with built-in WiFi (Pi 3/4/Zero W)
- Ethernet connection to Pi (optional, for internet access)
- SSH access to Pi

## Step 1: Install Required Packages

```bash
sudo apt update
sudo apt install hostapd dnsmasq -y
```

## Step 2: Configure Static IP for WiFi Interface

Edit dhcpcd configuration:

```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:

```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

Save and exit (Ctrl+X, Y, Enter)

## Step 3: Configure DHCP Server (dnsmasq)

Backup original config:

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

Create new config:

```bash
sudo nano /etc/dnsmasq.conf
```

Add the following:

```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.4.1
```

Save and exit.

## Step 4: Configure Access Point (hostapd)

Create hostapd configuration:

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add the following (customize ssid and wpa_passphrase):

```
interface=wlan0
driver=nl80211
ssid=RaspberryPi_AP
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=YourSecurePassword123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

**Important:** Change `wpa_passphrase` to a secure password of your choice!

Save and exit.

Tell system where to find config:

```bash
sudo nano /etc/default/hostapd
```

Find the line `#DAEMON_CONF=""` and replace with:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

Save and exit.

## Step 5: Enable Services

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
```

## Step 6: Reboot

```bash
sudo reboot
```

## Step 7: Verify Access Point

After reboot, you should see a WiFi network called `RaspberryPi_AP`. 

Check if services are running:

```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```

## Step 8: Configure ESP32 Master

Update these values in [Master_Node_Main.cpp](../../ESP32/src/Master_Node_Main.cpp):

```cpp
const char* WIFI_SSID = "RaspberryPi_AP";           // Your AP SSID
const char* WIFI_PASSWORD = "YourSecurePassword123"; // Your AP password
const char* MQTT_BROKER = "192.168.4.1";            // Pi's AP IP
```

## Troubleshooting

### Access Point not visible

```bash
# Check WiFi interface
iwconfig

# Check hostapd errors
sudo journalctl -u hostapd -f
```

### ESP32 can't connect

```bash
# Check connected devices
arp -a

# Monitor dnsmasq logs
sudo journalctl -u dnsmasq -f
```

### Restart services

```bash
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
```

## Notes

- The Pi will broadcast on **192.168.4.1**
- DHCP assigns IPs: **192.168.4.2 - 192.168.4.20**
- If you need internet on Pi, connect via Ethernet
- This setup does NOT provide internet to ESP32s (they don't need it)
