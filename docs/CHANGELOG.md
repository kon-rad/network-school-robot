# Changelog

## 2026-01-19: Documentation

Added comprehensive project documentation including a step-by-step local setup guide (SETUP.md) covering prerequisites, database configuration, backend and frontend installation, and troubleshooting tips, along with an architecture overview document (ARCHITECTURE.md) detailing the full-stack system design, technology stack, backend services, frontend components, API endpoints, data flows, and database schema.

## 2026-01-19: Live Camera Feed, Voice Control, and Robot Enhancements

This major update introduces a comprehensive voice control system with Deepgram speech-to-text integration, enabling users to interact with the robot through voice commands using wake word detection. The update adds live camera streaming capabilities with start/stop toggle controls, FPS display, and image capture/download functionality to the frontend CameraView component. New backend services include a Claude Code CLI executor for processing voice commands, text-to-speech (TTS) service, vision service for image analysis, and voice tracking for following audio sources. The robot service received significant enhancements including camera control methods, while new REST and WebSocket endpoints were added to support voice control features. Configuration was expanded to support the new voice control settings, and the frontend was updated with an improved UI for camera streaming and chat interface enhancements.
