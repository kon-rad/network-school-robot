# Reachy Mini Setup Guide

This guide covers connecting and controlling the Reachy Mini (Wireless) robot for use with the Network School Robot project.

## Hardware Versions

| Version | Price | Connection | Compute |
|---------|-------|------------|---------|
| **Reachy Mini Lite** | $299 | USB to your computer | External (your machine) |
| **Reachy Mini Wireless** | $449 | WiFi/Ethernet | Internal Raspberry Pi 4 |

---

## 1. Assembly

Reachy Mini comes as a kit. Building it is the first step of your journey!

- **Time required:** 2 to 3 hours
- **Tools:** Everything is included in the box
- **Instructions:** Follow the video guide alongside the manual

| Resource | Link |
|----------|------|
| Interactive Digital Guide | [Open Step-by-Step Guide](https://huggingface.co/spaces/pollen-robotics/Reachy_Mini_Assembly_Guide) |
| Full Assembly Video | [Watch on YouTube](https://www.youtube.com/watch?v=WeKKdnuXca4) |

---

## 2. First Boot & WiFi Configuration

Once assembled, you need to connect the robot to your WiFi network.

### Step 1: Power On

- Connect power via USB-C
- Green light indicates power
- Wait for the robot to boot (1-2 minutes)

### Step 2: Connect to Robot's WiFi Access Point

**Important:** Your computer must first connect to the robot's WiFi hotspot to configure it.

1. On your computer, look for WiFi network: **`reachy-mini-ap`**
2. Connect with password: **`reachy-mini`**

### Step 3: Configure Robot's WiFi

1. Open your browser and go to: **http://reachy-mini.local:8000/settings**
2. Enter your local WiFi credentials (SSID & Password)
3. Click **"Connect"**
4. Wait for Reachy Mini to connect to your WiFi network
5. The `reachy-mini-ap` access point will disappear once connected

> **Note:** If the connection fails, Reachy Mini will restart the access point and you can try again.

### Step 4: Connect Your Computer to the Same WiFi

**Critical:** Your computer must be on the **same WiFi network** as the robot to control it.

1. Disconnect from `reachy-mini-ap`
2. Connect your computer to the same WiFi network you configured for the robot
3. Wait for the robot to fully boot (1-2 minutes)

### Step 5: Verify Connection

Once both devices are on the same network:

- **Dashboard:** http://reachy-mini.local:8000
- **Settings:** http://reachy-mini.local:8000/settings
- **API Docs:** http://reachy-mini.local:8000/docs

If hostname doesn't resolve, find the robot's IP:
```bash
ping reachy-mini.local
# or check your router's DHCP client list
```

---

## 3. Update System

Before going further, update your robot to the latest version.

1. Go to **http://reachy-mini.local:8000/settings**
2. Click **"Check for updates"**
3. If available, follow on-screen instructions to install

---

## 4. Controlling the Robot

### Option 1: Robot Dashboard (Web UI)

Open http://reachy-mini.local:8000 in your browser for:
- Apps (conversation, games)
- WiFi settings
- Motor control
- Diagnostics

### Option 2: Network School Robot Interface

This project provides a custom interface for controlling the robot:

1. Start the backend server
2. Open http://localhost:5173
3. Use the **Debug** tab to send commands

### Option 3: REST API (Direct Control)

The robot exposes a REST API at port 8000:

```bash
# Check daemon status
curl http://reachy-mini.local:8000/api/daemon/status

# Enable motors
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled

# Move head
curl -X POST http://reachy-mini.local:8000/api/move/goto \
  -H "Content-Type: application/json" \
  -d '{"head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0}, "duration": 1.0}'

# Wake up animation
curl -X POST http://reachy-mini.local:8000/api/move/play/wake_up

# Sleep animation
curl -X POST http://reachy-mini.local:8000/api/move/play/goto_sleep
```

### Key REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/daemon/status` | GET | Daemon and backend status |
| `/api/daemon/restart` | POST | Restart the daemon |
| `/api/motors/status` | GET | Motor mode (enabled/disabled) |
| `/api/motors/set_mode/{mode}` | POST | Set motor mode |
| `/api/state/present_head_pose` | GET | Current head position |
| `/api/state/present_antenna_joint_positions` | GET | Antenna positions |
| `/api/move/goto` | POST | Move to target position |
| `/api/move/play/wake_up` | POST | Wake up animation |
| `/api/move/play/goto_sleep` | POST | Sleep animation |
| `/api/move/running` | GET | Currently running movements |
| `/api/move/stop` | POST | Stop all movements |

Full API docs: http://reachy-mini.local:8000/docs

---

## 5. SSH Access (Advanced)

Connect to Reachy Mini's internal Raspberry Pi:

```bash
ssh pollen@reachy-mini.local
# Password: root
```

Once connected, check system health:
```bash
reachyminios_check
```

---

## 6. Network School Robot Backend Configuration

Edit `backend/.env`:
```env
ROBOT_CONNECTION_MODE=network
ROBOT_HOST=192.168.1.9  # Use actual IP if hostname doesn't resolve
ROBOT_AUTO_CONNECT=true
```

---

## Troubleshooting

### Robot not found on network

1. **Verify same WiFi:** Ensure robot and computer are on the same network
2. **Check robot dashboard:** Try http://reachy-mini.local:8000
3. **Add to hosts file** (if mDNS not working):
   ```bash
   echo "192.168.1.9 reachy-mini.local reachy-mini" | sudo tee -a /etc/hosts
   ```
4. **Find IP via router:** Check your router's DHCP client list

### Backend not ready (`ready: false`)

1. Check daemon status:
   ```bash
   curl http://reachy-mini.local:8000/api/daemon/status
   ```
2. Restart daemon:
   ```bash
   curl -X POST http://reachy-mini.local:8000/api/daemon/restart
   ```
3. Enable motors:
   ```bash
   curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled
   ```

### SDK "Waiting for connection" timeout

The Python SDK uses Zenoh protocol for discovery. If it times out:

1. **Use REST API directly** (recommended for this project)
2. **Check Zenoh port:** `nc -zv reachy-mini.local 7447`
3. **Check macOS firewall:** System Settings → Privacy & Security → Firewall

### Robot not moving

1. **Enable motors:**
   ```bash
   curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled
   ```
2. **Check for running app:**
   ```bash
   curl http://reachy-mini.local:8000/api/apps/current-app-status
   ```

---

## Resources

- [Reachy Mini SDK (GitHub)](https://github.com/pollen-robotics/reachy_mini)
- [Pollen Robotics Website](https://www.pollen-robotics.com/reachy-mini/)
- [Pollen Robotics Discord](https://discord.gg/Y7FgMqHsub)
- [Assembly Guide](https://huggingface.co/spaces/pollen-robotics/Reachy_Mini_Assembly_Guide)
- [Assembly Video](https://www.youtube.com/watch?v=WeKKdnuXca4)
