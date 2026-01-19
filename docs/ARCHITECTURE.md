# Architecture Overview

Network School Robot is a full-stack application for controlling and interacting with a Reachy Mini robot through voice commands, chat, and a web dashboard.

## Project Overview

An AI-powered dashboard that enables Network School members to:
- Control the Reachy Mini robot through voice commands
- Chat with an AI assistant (Claude) that can execute robot actions
- View live camera feeds from the robot
- Monitor real-time logs and robot status

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Frontend (React 19 + TypeScript)                │
│                      http://localhost:5173                      │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Chat     │  │   Camera    │  │    Logs     │             │
│  │  Interface  │  │    View     │  │   Viewer    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP REST / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python)                       │
│                     http://localhost:8000                       │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Robot   │ │   Chat   │ │  Voice   │ │   Logs   │           │
│  │  Router  │ │  Router  │ │  Control │ │  Router  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                  │
│  ┌────▼────────────▼────────────▼────────────▼─────┐           │
│  │                   Services Layer                 │           │
│  │  Robot | Chat | Voice | STT | TTS | Vision      │           │
│  └──────────────────────────────────────────────────┘           │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────────────────┐
│  PostgreSQL   │ │  Reachy Mini  │ │    External Services      │
│  (Port 5433)  │ │    Robot      │ │  - Anthropic Claude API   │
│               │ │               │ │  - Deepgram STT/TTS       │
└───────────────┘ └───────────────┘ └───────────────────────────┘
```

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| asyncpg | 0.29+ | PostgreSQL async driver |
| Pydantic | 2.6+ | Data validation |
| Uvicorn | 0.27+ | ASGI server |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| TypeScript | 5.9 | Type safety |
| Vite | 7.2 | Build tool |
| TailwindCSS | 4.1 | Styling |
| React Query | 5.90 | Data fetching |
| Axios | 1.13 | HTTP client |

### External Services
| Service | Purpose |
|---------|---------|
| Anthropic Claude | AI chat and reasoning |
| Deepgram | Speech-to-text (STT) and text-to-speech (TTS) |
| Reachy Mini SDK | Robot hardware control |

### Database
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Logs, status, conversations |
| Docker Compose | Container orchestration |

---

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app setup, lifespan events
│   ├── config.py            # Pydantic settings, env variables
│   ├── database.py          # SQLAlchemy async setup
│   │
│   ├── models/
│   │   ├── robot_log.py     # Log entry model
│   │   └── conversation.py  # Chat history models
│   │
│   ├── routers/
│   │   ├── robot.py         # Robot control endpoints
│   │   ├── chat.py          # Claude conversation endpoints
│   │   ├── voice_control.py # Voice command endpoints
│   │   └── logs.py          # Log streaming endpoints
│   │
│   ├── services/
│   │   ├── robot_service.py          # Robot control logic
│   │   ├── chat_service.py           # Claude integration
│   │   ├── voice_control_service.py  # Voice pipeline
│   │   ├── stt_service.py            # Deepgram STT
│   │   ├── tts_service.py            # Deepgram TTS
│   │   ├── claude_code_service.py    # CLI executor
│   │   ├── command_parser_service.py # NLP parsing
│   │   ├── vision_service.py         # Image analysis
│   │   └── voice_tracking_service.py # Audio tracking
│   │
│   └── websocket/
│       └── manager.py       # WebSocket connection management
│
├── start.sh                 # Startup script with env setup
└── requirements.txt         # Python dependencies
```

### Services

#### RobotService
The main orchestrator for robot hardware interaction.

**Responsibilities:**
- Connection management (auto/localhost/network/simulation modes)
- Head movement with min-jerk trajectories
- Antenna control and expressions
- Audio recording and playback
- Camera frame capture
- Voice direction detection
- Heartbeat monitoring

#### ChatService
Manages conversations with Claude AI.

**Responsibilities:**
- Anthropic client management
- Conversation history tracking
- Action extraction from responses
- Model: `claude-sonnet-4-20250514`
- Personality: TARS from Interstellar (witty, honest)

#### VoiceControlService
Orchestrates the voice command pipeline.

**Responsibilities:**
- Coordinates STT, parsing, execution, and TTS
- Wake word detection ("hey claude", "claude code")
- State management (STOPPED, RUNNING, PROCESSING, SPEAKING)
- Event broadcasting via WebSocket

#### STTService
Speech-to-text using Deepgram.

**Responsibilities:**
- Real-time audio streaming
- Transcript callbacks (interim/final)
- Model: `nova-2`
- 16kHz mono PCM input

#### TTSService
Text-to-speech with robot playback.

**Responsibilities:**
- Voice synthesis via Deepgram API
- Voice: `aura-asteria-en`
- SSH/SCP to robot for audio playback
- Local macOS fallback (afplay)

#### ClaudeCodeService
Executes Claude Code CLI commands.

**Responsibilities:**
- Subprocess management
- Streaming output collection
- Process cancellation

#### CommandParserService
Natural language command parsing.

**Responsibilities:**
- Intent extraction
- Mode classification (ROBOT, CODE, CHAT)
- Parameter extraction

#### VisionService
Image analysis capabilities.

**Responsibilities:**
- Camera frame capture
- Base64 encoding
- Claude vision integration

#### VoiceTrackingService
Audio source tracking.

**Responsibilities:**
- Direction of arrival detection
- Head following with smoothing
- Automatic head movement toward speaker

---

## Frontend Architecture

### Component Hierarchy

```
App.tsx
├── Header
│   └── ConnectionIndicator
├── Sidebar
│   └── RobotStatus
└── Main Content (Tabs)
    ├── ChatInterface
    ├── CameraView
    └── LogViewer
```

### Components

| Component | Purpose |
|-----------|---------|
| `App.tsx` | Root component, tab navigation |
| `ChatInterface.tsx` | Chat messaging with Claude |
| `CameraView.tsx` | Live camera stream, capture |
| `RobotStatus.tsx` | Connection status, IMU data |
| `LogViewer.tsx` | Real-time log display |
| `ConnectionIndicator.tsx` | Header status badge |

### Services

**api.ts** - Centralized API client with methods for:
- Robot control (movement, emotions, camera, audio)
- Chat (messages, streaming, history)
- Logs (fetch, clear, WebSocket URL)

### Hooks

| Hook | Purpose |
|------|---------|
| `useWebSocket` | Log streaming with auto-reconnect |
| `useRobotStatus` | Robot status polling |

---

## API Endpoints

### Robot Control (`/api/robot`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Get connection status |
| POST | `/connect` | Connect to robot |
| POST | `/disconnect` | Disconnect from robot |
| POST | `/head/move` | Move head to position |
| POST | `/head/nod` | Nod gesture |
| POST | `/head/shake` | Shake head |
| POST | `/antennas/move` | Move antennas |
| POST | `/antennas/wiggle` | Wiggle antennas |
| POST | `/emotion` | Express emotion |
| POST | `/action` | Execute text action |
| POST | `/camera/start` | Start camera stream |
| POST | `/camera/stop` | Stop camera stream |
| POST | `/camera/capture` | Capture single frame |

### Chat (`/api/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Get config and robot status |
| POST | `/send` | Send message, get response |
| POST | `/stream` | Stream response (SSE) |
| POST | `/conversation` | Full conversation flow |
| GET | `/history` | Get conversation history |
| DELETE | `/history` | Clear history |

### Voice Control (`/api/voice-control`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Start voice control |
| POST | `/stop` | Stop voice control |
| GET | `/status` | Get status |
| POST | `/execute` | Manual command |
| WS | `/ws` | Real-time events |

### Logs (`/api/logs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Paginated logs |
| DELETE | `/` | Clear all logs |
| WS | `/stream` | Real-time streaming |

---

## Key Features

### Voice Control Pipeline

```
1. Audio Input
       │
       ▼
2. Deepgram STT ──────► Transcript
       │
       ▼
3. Wake Word Detection ("hey claude")
       │
       ▼
4. Command Parser ────► Intent + Mode
       │
       ▼
5. Claude Code CLI ───► Execution
       │
       ▼
6. Claude Response ───► Text + Actions
       │
       ▼
7. Deepgram TTS ──────► Audio
       │
       ▼
8. Robot Playback + Actions
```

### Chat with Actions

1. User sends message
2. Claude processes and responds
3. Actions extracted from `[action]` brackets
4. Actions executed sequentially
5. Results displayed in chat

### Camera Streaming

1. Frontend polls `/camera/capture` at ~5 FPS
2. Backend captures frame from robot
3. Frame encoded as base64 JPEG
4. Frontend displays in `<img>` tag
5. FPS counter shows actual rate

---

## Data Flow

### Chat Message Flow

```
User Input → ChatInterface → API → ChatService → Claude API
                                                     │
                                                     ▼
User Display ← ChatInterface ← API ← Actions ← Response
                                        │
                                        ▼
                                  RobotService
```

### Voice Command Flow

```
Microphone → STTService → CommandParser → ClaudeCodeService
                                                 │
                                                 ▼
Speaker ← TTSService ← ChatService ← Response ← Output
                            │
                            ▼
                      RobotService
```

---

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `robot_logs` | Activity and event logs |
| `robot_status` | Connection state |
| `conversations` | Chat session metadata |
| `conversation_messages` | Individual messages |

### Models

```python
# RobotLog
- id: UUID
- timestamp: DateTime
- level: String (INFO, WARN, ERROR, DEBUG)
- source: String
- message: Text
- metadata_: JSONB

# Conversation
- id: UUID
- user_id: String
- title: String
- created_at: DateTime
- updated_at: DateTime

# ConversationMessage
- id: UUID
- conversation_id: UUID (FK)
- role: String (user, assistant)
- content: Text
- created_at: DateTime
```

---

## Port Reference

| Service | Port | Protocol |
|---------|------|----------|
| Frontend | 5173 | HTTP |
| Backend | 8000 | HTTP/WS |
| PostgreSQL | 5433 | TCP |
| Robot SSH | 22 | TCP |

---

## Configuration

### Environment Variables

See [SETUP.md](./SETUP.md) for complete configuration details.

**Key Variables:**
- `ANTHROPIC_API_KEY` - Claude API access
- `DEEPGRAM_API_KEY` - Speech services
- `ROBOT_CONNECTION_MODE` - auto/localhost/network/simulation
- `DATABASE_URL` - PostgreSQL connection string

---

## Related Documentation

- [Setup Guide](./SETUP.md) - Local development setup
- [Changelog](./CHANGELOG.md) - Release history
