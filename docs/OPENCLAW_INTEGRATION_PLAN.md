# OpenClaw + Network School Robot Integration Plan

> Status: **DRAFT** - Not yet implemented
> Created: 2026-02-02

## Overview

Connect OpenClaw (running on DigitalOcean) with the robot backend to:
1. Route all chat through OpenClaw brain
2. Enable Telegram access via OpenClaw
3. Store memory in OpenClaw (replace Convex)
4. Allow OpenClaw to control robot via HTTP API

## Next Steps

1. **Current Plan** - OpenClaw skill calling robot backend (documented below)
2. **TODO: Research Alternative Approaches** - Explore other integration patterns

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DigitalOcean Server                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  OpenClaw Gateway                    │   │
│  │  - Brain (AI reasoning)                             │   │
│  │  - Memory (Markdown + SQLite)                       │   │
│  │  - Telegram Integration                             │   │
│  │                                                      │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │  robot-control skill                        │    │   │
│  │  │  - Calls robot backend via Tailscale VPN   │    │   │
│  │  │  - Receives events via WebSocket           │    │   │
│  │  └────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Tailscale VPN (encrypted)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Local Network (Robot)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Robot Backend (FastAPI :8000)                │   │
│  │                                                      │   │
│  │  NEW:                                               │   │
│  │  - POST /api/openclaw/command   (receive commands)  │   │
│  │  - WS /api/openclaw/events      (stream events)     │   │
│  │  - API key authentication                           │   │
│  │                                                      │   │
│  │  EXISTING (used by skill):                          │   │
│  │  - /api/robot/* (movement, camera, audio)           │   │
│  │  - /api/chat/send (TTS speaking)                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│                    Reachy Mini Robot                         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: Backend Authentication & Endpoints

**Files to create:**

1. `backend/app/routers/openclaw.py`
   - `POST /api/openclaw/command` - Receive commands from OpenClaw
   - `WS /api/openclaw/events` - Stream robot events
   - `GET /api/openclaw/status` - Health check

2. `backend/app/services/openclaw_auth.py`
   - API key validation middleware
   - Token stored in environment variable

3. `backend/app/services/event_broadcaster.py`
   - Broadcast robot events to connected WebSocket clients

**Files to modify:**

4. `backend/app/config.py`
   ```python
   # Add settings
   openclaw_enabled: bool = False
   openclaw_api_key: str = ""  # For authenticating incoming requests
   ```

5. `backend/app/main.py`
   - Include openclaw router

6. `backend/app/services/robot_service.py`
   - Add event broadcasting after each action

### Phase 2: OpenClaw Skill

**Create skill at:** `~/.openclaw/skills/robot-control/`

```
robot-control/
├── SKILL.md           # Skill definition
├── scripts/
│   └── robot.js       # Node.js script for API calls
└── package.json
```

**SKILL.md content:**
```markdown
---
name: robot-control
description: Control the Network School Reachy Mini robot
metadata: {"requires": {"env": ["ROBOT_API_URL", "ROBOT_API_KEY"]}}
---

# Robot Control

Control the physical robot remotely.

## Available Commands

Run scripts with: `node {baseDir}/scripts/robot.js <command> [args]`

Commands:
- `status` - Check robot connection
- `nod` - Nod head
- `shake` - Shake head
- `move <direction>` - Move head (up/down/left/right)
- `photo` - Take photo (returns base64)
- `speak <text>` - Speak through robot speakers
- `emotion <type>` - Express emotion (happy/sad/curious/surprised)
- `wiggle` - Wiggle antennas

Example: `node {baseDir}/scripts/robot.js speak "Hello from Telegram!"`
```

**scripts/robot.js:**
```javascript
#!/usr/bin/env node
const https = require('https');

const API_URL = process.env.ROBOT_API_URL;
const API_KEY = process.env.ROBOT_API_KEY;

async function callRobot(endpoint, method = 'POST', body = null) {
  const url = new URL(endpoint, API_URL);
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

const commands = {
  status: () => callRobot('/api/robot/status', 'GET'),
  nod: () => callRobot('/api/robot/head/nod'),
  shake: () => callRobot('/api/robot/head/shake'),
  move: (dir) => callRobot('/api/robot/action', 'POST', { action: `look ${dir}` }),
  photo: () => callRobot('/api/robot/camera/capture'),
  speak: (text) => callRobot('/api/chat/send', 'POST', { message: text, speak: true }),
  emotion: (type) => callRobot('/api/robot/emotion', 'POST', { emotion: type }),
  wiggle: () => callRobot('/api/robot/antennas/wiggle')
};

const [,, cmd, ...args] = process.argv;
if (commands[cmd]) {
  commands[cmd](args.join(' ')).then(r => console.log(JSON.stringify(r, null, 2)));
} else {
  console.log('Unknown command:', cmd);
}
```

### Phase 3: Tailscale VPN Setup

**On Robot Machine (Mac):**
```bash
# Install Tailscale
brew install tailscale

# Start and authenticate
sudo tailscale up

# Get Tailscale IP (e.g., 100.x.x.x)
tailscale ip -4
```

**On DigitalOcean Server:**
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start and authenticate (same Tailscale account)
sudo tailscale up

# Verify connection
tailscale status
# Should show robot machine in the list
```

**Configure OpenClaw skill:**
```bash
# Use Tailscale IP (e.g., 100.64.0.2)
export ROBOT_API_URL="http://100.64.0.2:8000"
export ROBOT_API_KEY="your-generated-key"
```

**Benefits of Tailscale:**
- Direct encrypted connection (no public exposure)
- Stable IPs that don't change
- Works through firewalls/NAT
- No monthly tunnel costs

### Phase 4: Memory Migration

1. Remove Convex message saving from `chat_service.py`
2. Keep local in-memory history for session context
3. OpenClaw stores all long-term memory in its markdown files

### Phase 5: Telegram Integration

1. Create Telegram bot via @BotFather
2. Add bot token to OpenClaw config
3. OpenClaw natively handles Telegram messages
4. User sends: "Robot, take a photo" → OpenClaw → Skill → Robot → Photo back

## Files Summary

| Action | File |
|--------|------|
| CREATE | `backend/app/routers/openclaw.py` |
| CREATE | `backend/app/services/openclaw_auth.py` |
| CREATE | `backend/app/services/event_broadcaster.py` |
| MODIFY | `backend/app/config.py` |
| MODIFY | `backend/app/main.py` |
| MODIFY | `backend/app/services/robot_service.py` |
| MODIFY | `backend/app/services/chat_service.py` |
| CREATE | `~/.openclaw/skills/robot-control/SKILL.md` |
| CREATE | `~/.openclaw/skills/robot-control/scripts/robot.js` |
| CREATE | `~/.openclaw/skills/robot-control/package.json` |

## Environment Variables

**Robot Backend (.env):**
```
OPENCLAW_ENABLED=true
OPENCLAW_API_KEY=your-secret-key-here
```

**OpenClaw (DigitalOcean):**
```
ROBOT_API_URL=http://100.64.0.2:8000  # Robot's Tailscale IP
ROBOT_API_KEY=your-secret-key-here
```

## Verification

1. Start robot backend with Tailscale running
2. Test skill locally: `node robot.js status`
3. Test via OpenClaw: Ask "check robot status"
4. Test via Telegram: Send "Robot, nod your head"
5. Verify photo capture returns image
6. Verify TTS speaks on robot

## Security Notes

- API key required for all robot commands
- Tailscale provides encrypted VPN connection (not publicly exposed)
- Robot backend only accessible to devices on your Tailscale network
- Whitelist Telegram user IDs in OpenClaw config
- Generate strong API key: `openssl rand -hex 32`

---

## Alternative Approaches to Research

> TODO: Research and document these alternatives

### Option A: MCP Server on Robot Backend
- Robot backend exposes MCP (Model Context Protocol) server
- OpenClaw connects via native MCP support
- More standardized integration pattern

### Option B: Robot Backend Calls OpenClaw API
- Reverse the direction: robot initiates connection
- Robot polls OpenClaw for commands
- Simpler networking (no inbound connections needed)

### Option C: Message Queue (Redis/NATS)
- Both services connect to cloud message queue
- Decoupled, scalable architecture
- Better handling of offline scenarios

### Option D: WebSocket Bridge Service
- Dedicated bridge service in cloud
- Both robot and OpenClaw connect outbound
- No direct connection between services

### Option E: OpenClaw on Same Machine as Robot
- Run OpenClaw locally alongside robot backend
- Simplest networking (localhost only)
- Requires Mac/Linux machine always running

---

## Research Notes

### What is OpenClaw?
- Open-source autonomous AI assistant (145k+ GitHub stars)
- Runs 24/7 autonomously
- Native integrations: Telegram, Discord, WhatsApp, iMessage
- Memory: Markdown files + SQLite (local per-device)
- Skills: YAML frontmatter + bash/Node/Python scripts
- MCP support for tool integrations

### Current Robot Stack
- FastAPI backend (Python)
- Reachy Mini SDK for hardware control
- OpenAI for chat, Claude for vision
- Deepgram STT, ElevenLabs TTS
- Convex for cloud storage (optional)
