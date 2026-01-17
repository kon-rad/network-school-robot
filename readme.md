# Network School Robot

An AI-powered dashboard for monitoring and controlling the Reachy Mini robot at Network School.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  Reachy Mini    │
│  (Port 5173)    │     │  (Port 8000)     │     │  Robot (SDK)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  PostgreSQL DB   │
                        │  (Port 5433)     │
                        └─────────────────┘
```

## Features

- Real-time robot status monitoring
- Live log streaming via WebSocket
- Robot connection/disconnection controls
- Persistent log storage in PostgreSQL
- Connection status indicators

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Reachy Mini robot (optional - runs in simulation mode without hardware)

## Quick Start

### 1. Start PostgreSQL Database

```bash
docker-compose up -d
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Dashboard

Open http://localhost:5173 in your browser.

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://robot_user:robot_password@localhost:5433/network_school_robot` |
| `ROBOT_CONNECTION_MODE` | Robot connection mode (auto, localhost_only, network) | `auto` |
| `TOGETHER_API_KEY` | Together AI API key for future LLM features | - |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

### Frontend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## API Endpoints

### Robot Control

- `GET /api/robot/status` - Get current robot status
- `POST /api/robot/connect` - Connect to robot
- `POST /api/robot/disconnect` - Disconnect from robot
- `GET /api/robot/info` - Get robot information

### Logs

- `GET /api/logs` - Get paginated logs
- `DELETE /api/logs` - Clear log history
- `WS /api/logs/stream` - WebSocket for real-time logs

### Health

- `GET /` - API info
- `GET /health` - Health check

## Project Structure

```
network-school-robot/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # Database connection
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   └── websocket/       # WebSocket manager
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   └── App.tsx
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Database Migrations

The database tables are created automatically on startup. For production, consider using Alembic migrations.

## Reachy Mini Robot

This project integrates with the [Reachy Mini robot](https://github.com/pollen-robotics/reachy_mini) from Pollen Robotics.

### Connection Modes

- **auto** (default): Auto-detects connection via USB or network
- **localhost_only**: USB/localhost connection only
- **network**: Network connection only
- **simulation**: Runs without hardware (for development)

## Future Enhancements

- Together AI integration for coaching conversations
- User authentication and sessions
- Robot movement controls
- Camera feed streaming
- Audio recording/playback
- Discord/Luma calendar integration

## License

MIT
