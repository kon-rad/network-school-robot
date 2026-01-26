# Changelog

## 2026-01-21: Personality System, Video Streaming, and Multiple Service Integrations

This release introduces a comprehensive personality system with 8 AI personas (TARS, Samantha, JARVIS, Coach, Teacher, Friend, Expert, Therapist), allowing users to interact with different AI personalities tailored to various needs.

### New Features

- **Personality System** - 8 distinct AI personas with unique characteristics and interaction styles
- **High-FPS Video Streaming** - WebSocket-based video streaming targeting 60 FPS for smooth real-time camera feeds
- **Token Minting & Rewards** - New token system for minting and distributing rewards to users
- **AWS S3 Storage Integration** - Cloud storage for photos and videos captured by the robot
- **Convex Backend Integration** - Message storage and synchronization via Convex database
- **Person Recognition** - OpenCV combined with Gemini Vision for identifying and recognizing people
- **ElevenLabs TTS** - Enhanced text-to-speech using ElevenLabs voice synthesis

### Changes

- **Chat API Migration** - Switched chat backend from Anthropic to OpenAI API
- **WebSocket Video Streaming** - Replaced HTTP-based camera streaming with WebSocket for better performance
- **Frontend CameraView** - Updated to support WebSocket streaming with improved frame handling
- **ChatInterface** - Updated references to reflect OpenAI integration

### New Backend Components

**Routers:**
- `personality.py` - Personality selection and management endpoints
- `tokens.py` - Token minting, balance, and transaction endpoints
- `storage.py` - S3 storage upload/download endpoints
- `recognition.py` - Person recognition and identification endpoints

**Services:**
- `personality_service.py` - AI persona management and prompt customization
- `token_service.py` - Token minting, transfers, and balance tracking
- `storage_service.py` - AWS S3 integration for media storage
- `convex_service.py` - Convex database operations for message persistence
- `video_stream_service.py` - WebSocket-based high-FPS video streaming
- `person_recognition_service.py` - OpenCV + Gemini Vision person identification

### Files Changed

- 21 files modified
- +2,560 lines added / -195 lines removed

## 2026-01-19: Documentation

Added comprehensive project documentation including a step-by-step local setup guide (SETUP.md) covering prerequisites, database configuration, backend and frontend installation, and troubleshooting tips, along with an architecture overview document (ARCHITECTURE.md) detailing the full-stack system design, technology stack, backend services, frontend components, API endpoints, data flows, and database schema.

## 2026-01-19: Live Camera Feed, Voice Control, and Robot Enhancements

This major update introduces a comprehensive voice control system with Deepgram speech-to-text integration, enabling users to interact with the robot through voice commands using wake word detection. The update adds live camera streaming capabilities with start/stop toggle controls, FPS display, and image capture/download functionality to the frontend CameraView component. New backend services include a Claude Code CLI executor for processing voice commands, text-to-speech (TTS) service, vision service for image analysis, and voice tracking for following audio sources. The robot service received significant enhancements including camera control methods, while new REST and WebSocket endpoints were added to support voice control features. Configuration was expanded to support the new voice control settings, and the frontend was updated with an improved UI for camera streaming and chat interface enhancements.
