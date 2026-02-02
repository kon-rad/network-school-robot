# Network School Robot

An AI-powered Reachy Mini robot that serves as a personal coach, conversational companion, and interactive assistant for the Network School community.

## Codebase Overview

**Stack:** FastAPI (Python) + React (TypeScript) + Reachy Mini SDK + Multiple AI Services

**Architecture:** User speaks → Deepgram STT → AI (OpenAI/Claude) → Actions extracted → Robot moves + TTS responds

**Key Innovation:** AI responses include bracketed actions like `[nod]` or `[wiggle antennas]` that are parsed and executed on the physical robot.

For detailed architecture, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).

## Quick Reference

| Component | Location | Purpose |
|-----------|----------|---------|
| Robot control | `backend/app/services/robot_service.py` | Reachy Mini SDK interface |
| AI chat | `backend/app/services/chat_service.py` | OpenAI + action extraction |
| Voice control | `backend/app/services/voice_control_service.py` | Wake word → command flow |
| Personalities | `backend/app/services/personality_service.py` | 8 AI personas (TARS, Samantha, etc.) |
| Vision | `backend/app/services/vision_service.py` | Claude image analysis |

## Project Purpose

A conversational robot that helps Network School members with:

- **Life & Business Coaching** - Goal setting, accountability, feedback on ideas and plans
- **Network School Knowledge** - Information about NS programs, culture, and resources
- **Logistics** - Practical questions about living/working at Network School
- **Daily Check-ins** - Build a relationship over time with context memory

## Core Philosophy

- Be a supportive friend that remembers you
- Express through physical movement (head, antennas, body)
- Provide honest, constructive feedback via distinct AI personalities
- Help members get the most out of their Network School experience

## Key Commands

```bash
# Start robot daemon
curl -X POST "http://reachy-mini.local:8000/api/daemon/start?wake_up=true"

# Run backend
cd backend && ./start.sh

# Run frontend
cd frontend && npm run dev
```

## Development Guidelines

- Action syntax: Use `[action name]` in AI prompts for robot execution
- Wake words: "hey claude", "claude code"
- Camera triggers: "take a picture", "what do you see"
- Personalities affect voice, temperature, and system prompt
