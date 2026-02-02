# Local Setup Guide

Step-by-step instructions to run the Network School Robot application locally.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/)

**API Keys Required:**
- **OpenAI API Key** - For chat integration ([Get key](https://platform.openai.com/))
- **Deepgram API Key** - For speech-to-text ([Get key](https://console.deepgram.com/))

**API Keys Optional:**
- **ElevenLabs API Key** - For enhanced text-to-speech ([Get key](https://elevenlabs.io/))
- **Gemini API Key** - For person recognition with Vision ([Get key](https://aistudio.google.com/))
- **AWS Credentials** - For S3 photo/video storage
- **Convex URL** - For message persistence ([Get started](https://convex.dev/))

**macOS Only:**
```bash
brew install gstreamer gst-plugins-base gst-plugins-good
```

---

## Quick Start

For experienced developers:

```bash
# 1. Start database
docker-compose up -d

# 2. Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
# Edit .env with your API keys
./start.sh

# 3. Frontend (new terminal)
cd frontend && npm install && npm run dev

# 4. Open http://localhost:5173
```

---

## Step 1: Start the Database

The application uses PostgreSQL for storing logs, robot status, and conversations.

```bash
# From the project root directory
docker-compose up -d
```

Verify the database is running:
```bash
docker-compose ps
```

You should see the `postgres` container with status `Up`.

> **Note:** The database is optional. The application will work without it but won't persist logs or conversation history.

---

## Step 2: Setup the Backend

### 2.1 Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your API keys:

```env
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
DEEPGRAM_API_KEY=your-deepgram-key-here

# Optional API Keys
ELEVENLABS_API_KEY=your-elevenlabs-key-here
GEMINI_API_KEY=your-gemini-key-here

# AWS S3 Storage (optional - for photo/video storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Convex Backend (optional - for message persistence)
CONVEX_URL=your-convex-deployment-url

# Database (optional - uses Docker Compose settings)
DATABASE_URL=postgresql+asyncpg://robot_user:robot_password@localhost:5433/network_school_robot

# Robot Configuration
ROBOT_CONNECTION_MODE=simulation    # Use 'simulation' if no robot hardware
ROBOT_HOST=reachy-mini.local        # Robot hostname (if using hardware)
ROBOT_AUTO_CONNECT=false            # Set to true to auto-connect on startup

# Personality (tars, samantha, jarvis, coach, teacher, friend, expert, therapist)
DEFAULT_PERSONALITY=tars

# CORS (frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Voice Control
VOICE_CONTROL_ENABLED=true
VOICE_CONTROL_AUTO_START=false
```

### 2.4 Start the Backend Server

```bash
./start.sh
```

Or manually:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

## Step 3: Setup the Frontend

Open a new terminal window.

### 3.1 Install Dependencies

```bash
cd frontend
npm install
```

### 3.2 Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Step 4: Access the Application

Open your browser and navigate to:

**http://localhost:5173**

You should see the Network School Robot dashboard with:
- **Chat** - Interact with the AI assistant (supports 8 different AI personalities)
- **Camera** - View live camera feed via WebSocket streaming (requires robot)
- **Logs** - View real-time activity logs

### Available Personalities

The robot supports 8 AI personas selectable via the `DEFAULT_PERSONALITY` env var or API:

| Personality | Description |
|-------------|-------------|
| `tars` | TARS from Interstellar - witty, helpful, adjustable humor |
| `samantha` | Samantha from Her - warm, emotionally intelligent |
| `jarvis` | JARVIS from Iron Man - professional, efficient butler |
| `coach` | Motivational life coach |
| `teacher` | Patient, educational instructor |
| `friend` | Casual, supportive companion |
| `expert` | Technical expert, precise and detailed |
| `therapist` | Empathetic, reflective counselor |

---

## Port Reference

| Service    | Port | URL                     |
|------------|------|-------------------------|
| Frontend   | 5173 | http://localhost:5173   |
| Backend    | 8000 | http://localhost:8000   |
| PostgreSQL | 5433 | localhost:5433          |

---

## Running with Robot Hardware (Optional)

If you have a Reachy Mini robot:

### Connecting to the Robot

#### Scenario A: Robot Already Configured (Most Common)

If you've used the robot before, it may already be on your WiFi network:

```bash
# 1. Check if robot is reachable
ping reachy-mini.local

# 2. If reachable, check daemon status
curl http://reachy-mini.local:8000/api/daemon/status

# 3. If state is "not_initialized", start the daemon
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"

# 4. Wait 5-10 seconds, then verify it's running
curl http://reachy-mini.local:8000/api/daemon/status
# Should show: "state": "running"
```

#### Scenario B: First-Time Setup (WiFi Access Point)

If the robot is brand new or was factory reset:

1. **Power on the robot** via USB-C (green light = power on)
2. **Wait 1-2 minutes** for full boot
3. **Look for WiFi network:** `reachy-mini-ap`
4. **Connect with password:** `reachy-mini`
5. **Open browser:** http://reachy-mini.local:8000/settings
6. **Enter your WiFi credentials** and click Connect
7. **Switch your computer** to the same WiFi network
8. **Verify connection:** `ping reachy-mini.local`

> **Note:** The `reachy-mini-ap` access point disappears once the robot connects to your WiFi.

#### Scenario C: Robot Not Found

If ping fails and no `reachy-mini-ap` WiFi is visible:

```bash
# 1. Check your router's DHCP client list for a device named "reachy-mini"

# 2. If you find the IP (e.g., 192.168.1.28), add to hosts file:
echo "192.168.1.28 reachy-mini.local reachy-mini" | sudo tee -a /etc/hosts

# 3. Or use the IP directly in your .env:
ROBOT_HOST=192.168.1.28
```

### Configure Connection Mode

Edit `backend/.env`:

```env
# Connection modes:
# - auto: Try localhost first, then network
# - localhost_only: Only connect via localhost
# - network: Connect via network hostname
# - simulation: No hardware (mock responses)

ROBOT_CONNECTION_MODE=network
ROBOT_HOST=reachy-mini.local  # or use IP: 192.168.1.28
ROBOT_AUTO_CONNECT=true
```

### Quick Robot Commands Reference

```bash
# Check daemon status
curl http://reachy-mini.local:8000/api/daemon/status

# Start daemon (with wake up animation)
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"

# Restart daemon
curl -X POST http://reachy-mini.local:8000/api/daemon/restart

# Enable motors
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled

# Play wake up animation
curl -X POST http://reachy-mini.local:8000/api/move/play/wake_up

# Sleep animation
curl -X POST http://reachy-mini.local:8000/api/move/play/goto_sleep

# Check current app running
curl http://reachy-mini.local:8000/api/apps/current-app-status
```

### macOS GStreamer Setup

The `start.sh` script automatically configures GStreamer paths. If running manually:

```bash
export GST_PLUGIN_PATH="/opt/homebrew/lib/gstreamer-1.0"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

---

## Troubleshooting

### Database Connection Error

**Error:** `connection refused` or `database does not exist`

**Solution:**
```bash
# Restart the database
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs postgres
```

### Backend Won't Start

**Error:** Module not found

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### API Key Errors

**Error:** `401 Unauthorized` or `Invalid API key`

**Solution:**
- Verify your API keys in `backend/.env`
- Ensure keys don't have extra spaces or quotes
- Check that your OpenAI/Deepgram accounts are active
- For optional features, ensure respective API keys are set (ElevenLabs for TTS, Gemini for person recognition)

### Robot Connection Failed

**Error:** `Could not connect to robot`

**Solution:**
1. Set `ROBOT_CONNECTION_MODE=simulation` to run without hardware
2. If using hardware, ensure the robot is powered on and on the same network
3. Verify `ROBOT_HOST` matches your robot's hostname

### Robot Found But Not Responding

**Error:** Robot pingable but API calls fail or motors won't move

**Solution:**
```bash
# 1. Check daemon status
curl http://reachy-mini.local:8000/api/daemon/status

# If state is "not_initialized":
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"

# If backend_status.ready is false, wait 10 seconds and check again

# 2. Enable motors if needed
curl -X POST http://reachy-mini.local:8000/api/motors/set_mode/enabled

# 3. Try wake up animation to verify
curl -X POST http://reachy-mini.local:8000/api/move/play/wake_up
```

### Can't Find Robot WiFi (reachy-mini-ap)

**Problem:** Robot powered on but no `reachy-mini-ap` WiFi network appears

**Solution:**
1. **Robot already configured:** Try `ping reachy-mini.local` - it may already be on your network
2. **Not booted yet:** Wait 2 minutes after power on for full boot
3. **Check router:** Look in your router's DHCP list for "reachy-mini"
4. **Factory reset:** If needed, SSH into robot and reset WiFi settings (see REACHY_MINI_SETUP.md)

### Frontend Can't Connect to Backend

**Error:** Network error or CORS error

**Solution:**
1. Ensure the backend is running on port 8000
2. Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`
3. Try restarting both backend and frontend

---

## Next Steps

- Read the [Architecture Documentation](./ARCHITECTURE.md) to understand the system design
- Check the [Changelog](./CHANGELOG.md) for recent updates
- Explore the API at `http://localhost:8000/docs` (Swagger UI)
