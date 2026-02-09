# Getting Started

This guide walks you through starting the full application stack and connecting to a Reachy Mini robot via USB-C.

---

## 1. Start the Database

The app uses PostgreSQL via Docker for logs, conversations, and robot status.

```bash
# From the project root
docker-compose up -d

# Verify it's running
docker-compose ps
# Should show: network-school-robot-db ... Up
```

---

## 2. Start the Backend

```bash
cd backend
source venv/bin/activate
./start.sh
```

> **First time?** Create the venv first — you must use **Python 3.13** (not 3.14):
> ```bash
> python3.13 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> cp .env.example .env   # then edit .env with your API keys
> ```

The backend runs at **http://localhost:8000**. API docs at **http://localhost:8000/docs**.

---

## 3. Start the Frontend

In a separate terminal:

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 4. Connect to Reachy Mini via USB-C

Plug in the Reachy Mini with the USB-C cable. The steps differ depending on which model you have.

### Which model do I have?

| | Reachy Mini Lite ($299) | Reachy Mini Wireless ($449) |
|---|---|---|
| **Compute** | None — your computer does everything | Internal Raspberry Pi 4 |
| **USB devices** | Camera, Audio, Serial (3 devices) | Camera, Audio, Serial + USB Ethernet (4 devices) |
| **Onboard web server** | No | Yes — `reachy-mini.local:8000` |
| **Connection mode** | `usb` or `localhost_only` | `network` (WiFi) or `usb` (USB-C) |

Check which USB devices appear:

```bash
system_profiler SPUSBDataType 2>/dev/null | grep -A 2 "Reachy\|pollen"
```

You should see **Reachy Mini Camera**, **Reachy Mini Audio**, and a **USB Single Serial** device.

---

### Option A: Reachy Mini Lite (USB-C only)

The Lite has no onboard computer. Your machine controls the robot directly through the USB serial port.

#### Step 1: Verify USB serial port

```bash
ls /dev/cu.usbmodem*
```

You should see something like `/dev/cu.usbmodem5AF71346861`. This is the motor control serial port.

#### Step 2: Configure backend `.env`

Edit `backend/.env`:

```env
ROBOT_CONNECTION_MODE=usb
ROBOT_HOST=localhost
ROBOT_AUTO_CONNECT=true
```

#### Step 3: Restart the backend

```bash
cd backend
source venv/bin/activate
./start.sh
```

The `reachy-mini` Python SDK will discover the robot automatically via the USB serial port. No daemon or web server is involved — your backend talks directly to the motors, camera, and audio.

#### Step 4: Verify connection

Open **http://localhost:5173** and check the robot status in the UI, or:

```bash
# Check connection via your backend API
curl http://localhost:8000/api/robot/status
```

---

### Option B: Reachy Mini Wireless via USB-C

The Wireless model has a Raspberry Pi inside. When connected via USB-C, it creates a USB Ethernet network interface on your Mac.

#### Step 1: Check for USB Ethernet interface

```bash
ifconfig | grep -A 5 "inet 192.168.186"
```

If you see an interface with an IP in the `192.168.186.x` range, the USB Ethernet is working. The robot is typically at `192.168.186.2`.

If no USB Ethernet interface appears, the robot may need to be configured for USB networking first (see Troubleshooting below).

#### Step 2: Verify robot is reachable

```bash
# Try hostname first
ping reachy-mini.local

# If hostname doesn't resolve, try the USB Ethernet IP
ping 192.168.186.2
```

#### Step 3: Check the robot's daemon

```bash
# Use whichever address worked above
curl http://reachy-mini.local:8000/api/daemon/status
```

If the state is `"not_initialized"`, start it:

```bash
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"
```

Wait 10 seconds, then verify:

```bash
curl http://reachy-mini.local:8000/api/daemon/status
# Should show: "state": "running"
```

#### Step 4: Configure backend `.env`

Edit `backend/.env`:

```env
ROBOT_CONNECTION_MODE=network
ROBOT_HOST=reachy-mini.local    # or 192.168.186.2 if hostname doesn't resolve
ROBOT_AUTO_CONNECT=true
```

#### Step 5: Restart the backend

```bash
cd backend
source venv/bin/activate
./start.sh
```

#### Step 6: Verify connection

```bash
curl http://localhost:8000/api/robot/status
```

---

### Option C: Reachy Mini Wireless via WiFi

If you prefer WiFi over USB-C (or are using the robot across the room):

#### Step 1: First-time WiFi setup

1. Power on the robot via USB-C (green light = power on)
2. Wait 1-2 minutes for full boot
3. On your computer, connect to WiFi network: **`reachy-mini-ap`** (password: **`reachy-mini`**)
4. Open browser: **http://reachy-mini.local:8000/settings**
5. Enter your local WiFi SSID and password, click Connect
6. Switch your computer back to the same WiFi network
7. Wait 1-2 minutes for the robot to reconnect

#### Step 2: Verify connection

```bash
ping reachy-mini.local
curl http://reachy-mini.local:8000/api/daemon/status
```

#### Step 3: Start daemon if needed

```bash
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"
```

#### Step 4: Configure backend `.env`

```env
ROBOT_CONNECTION_MODE=network
ROBOT_HOST=reachy-mini.local
ROBOT_AUTO_CONNECT=true
```

---

## 5. Running Without a Robot

If you don't have hardware, run in simulation mode:

```env
# backend/.env
ROBOT_CONNECTION_MODE=simulation
ROBOT_AUTO_CONNECT=false
```

The app will work normally — chat, personalities, and voice control all function. Robot movements will be logged but not physically executed.

---

## Quick Robot Commands

Once connected to a Wireless model, these commands control the robot directly:

```bash
# Enable motors
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled

# Wake up animation
curl -X POST http://reachy-mini.local:8000/api/move/play/wake_up

# Sleep animation
curl -X POST http://reachy-mini.local:8000/api/move/play/goto_sleep

# Move head
curl -X POST http://reachy-mini.local:8000/api/move/goto \
  -H "Content-Type: application/json" \
  -d '{"head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0}, "duration": 1.0}'

# Check what's running
curl http://reachy-mini.local:8000/api/apps/current-app-status

# Stop all movements
curl -X POST http://reachy-mini.local:8000/api/move/stop
```

---

## SSH Access (Wireless Only)

For advanced debugging on the Wireless model:

```bash
ssh pollen@reachy-mini.local
# Password: root

# Check system health
reachyminios_check
```

---

## Troubleshooting

### `reachy-mini.local` doesn't resolve

1. Check your router's DHCP client list for a device named "reachy-mini"
2. If you find the IP, add it to your hosts file:
   ```bash
   echo "192.168.1.28 reachy-mini.local reachy-mini" | sudo tee -a /etc/hosts
   ```
3. Or use the IP directly in `ROBOT_HOST`

### No USB serial port appears (Lite)

- Check that the USB-C cable supports data (not charge-only)
- Try a different USB-C port
- Run `system_profiler SPUSBDataType` and look for "Reachy Mini" devices

### scipy fails to install

You're likely using Python 3.14. Recreate the venv with Python 3.13:

```bash
cd backend
deactivate
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Robot daemon won't start

```bash
# Restart the daemon
curl -X POST http://reachy-mini.local:8000/api/daemon/restart

# If that fails, SSH in and check logs
ssh pollen@reachy-mini.local
journalctl -u reachy-mini -n 50
```

### Robot not moving after connection

```bash
# Make sure motors are enabled
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled

# Check if another app has control
curl http://reachy-mini.local:8000/api/apps/current-app-status
```

### macOS firewall blocking connection

Go to **System Settings > Privacy & Security > Firewall** and either disable it or add exceptions for the backend and Zenoh protocol (port 7447).

---

## Connection Mode Reference

| Mode | `ROBOT_CONNECTION_MODE` | `ROBOT_HOST` | Use Case |
|------|------------------------|--------------|----------|
| USB Lite | `usb` | `localhost` | Reachy Mini Lite via USB-C |
| USB Wireless | `network` | `192.168.186.2` | Reachy Mini Wireless via USB-C |
| WiFi | `network` | `reachy-mini.local` | Reachy Mini Wireless via WiFi |
| Auto | `auto` | `reachy-mini.local` | Try localhost then network |
| No hardware | `simulation` | (any) | Development without robot |
