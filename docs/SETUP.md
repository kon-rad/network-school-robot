# Local Setup Guide

Step-by-step instructions to run the Network School Robot application locally.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.13** (required — Python 3.14 does not have pre-built wheels for scipy/reachy-mini)
  - Install via Homebrew: `brew install python@3.13`
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/)

**macOS Only (GStreamer for audio/video):**
```bash
brew install gstreamer gst-plugins-base gst-plugins-good
```

**API Keys Required:**
- **OpenAI API Key** - For chat integration ([Get key](https://platform.openai.com/))
- **Deepgram API Key** - For speech-to-text ([Get key](https://console.deepgram.com/))

**API Keys Optional:**
- **Anthropic API Key** - For Claude-powered chat and vision ([Get key](https://console.anthropic.com/))
- **ElevenLabs API Key** - For enhanced text-to-speech ([Get key](https://elevenlabs.io/))
- **Gemini API Key** - For person recognition with Vision ([Get key](https://aistudio.google.com/))
- **Together AI API Key** - For additional AI models
- **AWS Credentials** - For S3 photo/video storage
- **Convex URL** - For message persistence ([Get started](https://convex.dev/))

---

## Reachy Mini Hardware Versions

This project supports both Reachy Mini models:

| Version | Price | Connection | Compute | Has Onboard Server? |
|---------|-------|------------|---------|---------------------|
| **Reachy Mini Lite** | $299 | USB-C to your computer | Your machine | No |
| **Reachy Mini Wireless** | $449 | WiFi/Ethernet + USB-C | Internal Raspberry Pi 4 | Yes (port 8000) |

**Key difference:** The Lite has no onboard computer — your machine controls everything directly via USB serial. The Wireless has a Raspberry Pi that runs a daemon and web server at `reachy-mini.local:8000`.

For detailed robot connection instructions, see [GETTING_STARTED.md](../GETTING_STARTED.md).

---

## Quick Start

For experienced developers:

```bash
# 1. Start database
docker-compose up -d

# 2. Backend
cd backend
python3.13 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys and robot connection mode
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

You should see the `network-school-robot-db` container with status `Up`.

> **Note:** The database is optional. The application will work without it but won't persist logs or conversation history.

---

## Step 2: Setup the Backend

### 2.1 Create Virtual Environment

**Important:** Use Python 3.13 specifically. Python 3.14 will fail building scipy.

```bash
cd backend

# Create virtual environment with Python 3.13
python3.13 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
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
ANTHROPIC_API_KEY=your-anthropic-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
GEMINI_API_KEY=your-gemini-key-here
TOGETHER_AI_API_KEY=your-together-ai-key-here

# AWS S3 Storage (optional - for photo/video storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Convex Backend (optional - for message persistence)
CONVEX_URL=your-convex-deployment-url

# Database (uses Docker Compose settings)
DATABASE_URL=postgresql+asyncpg://robot_user:robot_password@localhost:5433/network_school_robot

# Robot Configuration (see GETTING_STARTED.md for details)
ROBOT_CONNECTION_MODE=simulation    # Options: usb, network, auto, localhost_only, simulation
ROBOT_HOST=reachy-mini.local        # Robot hostname (if using hardware)
ROBOT_AUTO_CONNECT=true

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

The `start.sh` script automatically sets up GStreamer paths for macOS. If running manually:
```bash
export GST_PLUGIN_PATH="/opt/homebrew/lib/gstreamer-1.0"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
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

## Troubleshooting

### scipy / reachy-mini Install Fails

**Error:** `Dependency "OpenBLAS" not found` or `metadata-generation-failed` for scipy

**Cause:** You're using Python 3.14 which lacks pre-built scipy wheels.

**Solution:**
```bash
# Recreate venv with Python 3.13
deactivate
rm -rf venv
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database Connection Error

**Error:** `connection refused` or `database does not exist`

**Solution:**
```bash
docker-compose down
docker-compose up -d
docker-compose logs postgres
```

### Backend Won't Start

**Error:** Module not found

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Errors

**Error:** `401 Unauthorized` or `Invalid API key`

**Solution:**
- Verify your API keys in `backend/.env`
- Ensure keys don't have extra spaces or quotes
- Check that your OpenAI/Deepgram accounts are active

### Robot Connection Failed

**Error:** `Could not connect to robot`

**Solution:**
1. Set `ROBOT_CONNECTION_MODE=simulation` to run without hardware
2. If using hardware, see [GETTING_STARTED.md](../GETTING_STARTED.md) for connection steps

### Frontend Can't Connect to Backend

**Error:** Network error or CORS error

**Solution:**
1. Ensure the backend is running on port 8000
2. Check `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`
3. Try restarting both backend and frontend

---

## Next Steps

- Read [GETTING_STARTED.md](../GETTING_STARTED.md) for robot hardware connection
- Read the [Architecture Documentation](./ARCHITECTURE.md) to understand the system design
- Check the [Changelog](./CHANGELOG.md) for recent updates
- Explore the API at `http://localhost:8000/docs` (Swagger UI)
