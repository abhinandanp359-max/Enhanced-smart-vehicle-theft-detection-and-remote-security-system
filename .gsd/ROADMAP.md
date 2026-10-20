# ROADMAP.md — Smart Vehicle Theft Detection & Remote Security System

> **Milestone**: M1 - Working Safe Prototype
> **Status**: Planning (Awaiting User Approval)

## Phase Breakdown

### Phase 1: Architecture, Contracts & Development Environment Setup
- **Goal**: Establish monorepo structure, data models, API/WebSocket contracts, shared types, and mock providers.
- **Deliverables**:
  - Monorepo skeleton (`backend/`, `frontend/`, `ai_engine/`, `simulator/`).
  - Environment configurations (`.env.example` across services).
  - Database schemas and Mongoose models (`User`, `Vehicle`, `SecurityEvent`, `TrackingSession`).
  - Provider abstractions for Camera, GPS, Alarm.
- **Exit Criteria**: Services build cleanly; database connects; contracts defined.

### Phase 2: Backend Core & Real-Time Socket Gateway
- **Goal**: Implement complete REST API and Socket.io real-time coordination layer.
- **Deliverables**:
  - JWT Authentication & RBAC (Owner & Trusted Driver).
  - Vehicle management endpoints & Security Mode state transitions (`ARMED`, `OFF`, `TRUSTED_DRIVER`).
  - Evidence upload handler (Multer) with static asset serving.
  - Bidirectional Socket.io rooms: `vehicle:{id}` and `owner:{id}` with events (`STATE_SYNC`, `THEFT_ALERT`, `LIVE_GPS_UPDATE`, `DISARM_COMMAND`).
- **Exit Criteria**: Postman/curl and socket test client can arm, disarm, upload evidence, and receive socket broadcasts.

### Phase 3: AI Computer Vision & Theft Decision Engine
- **Goal**: Build Python-based YOLOv8 + OpenCV edge service with robust anti-false-alarm logic.
- **Deliverables**:
  - Video stream pipeline (Webcam / IP Cam / Video File test fallback).
  - YOLOv8n inference loop with Driver-Seat ROI polygon filtering.
  - Multi-factor Theft State Machine: Temporal accumulator (e.g. 3-5 seconds sustained presence), confidence thresholding, and mode gating.
  - Local alarm sound generator (siren playback on speaker/buzzer).
  - Evidence capturer (annotated JPEG + short circular buffer MP4).
  - Backend integration client: auto-dispatches incident payload and activates GPS simulator.
- **Exit Criteria**: Standing in front of webcam in armed mode triggers sustained detection -> local siren rings -> snapshot and incident payload automatically posted to backend.

### Phase 4: Dynamic GPS & Vehicle Telemetry Simulator
- **Goal**: Implement realistic vehicle route simulation and live tracking pipeline.
- **Deliverables**:
  - Algorithmic route interpolator (waypoints along a simulated city path).
  - Dynamic telemetry emission (speed, heading, latitude, longitude) triggered on theft event.
  - Ingestion and relay over Socket.io to frontend subscribers.
- **Exit Criteria**: Backend receives periodic GPS packets post-theft and relays them to connected clients with <100ms latency.

### Phase 5: Mobile-First Responsive Owner Application (Frontend)
- **Goal**: Deliver a futuristic, ultra-responsive dark-mode dashboard optimized for mobile and desktop.
- **Deliverables**:
  - Visual Design System: bespoke automotive cyber-security aesthetic (dark slate/carbon glassmorphism, pulse animations, neon badges).
  - Screen 1: Auth & Vehicle Setup.
  - Screen 2: Central Command Dashboard (Interactive Arm/Disarm slider, live system telemetry, camera preview stream).
  - Screen 3: Emergency Alert Modal / Screen (Urgent siren sound, animated warning, captured evidence image/video viewer, 1-tap "DISARM/SILENCE", "CALL AUTHORITIES").
  - Screen 4: Live GPS Tracking Screen (Interactive Leaflet map, animated vehicle pin, breadcrumb trail, speed gauge).
  - Screen 5: Incident History & Evidence Vault (Search, filter, full-res image modal, download report).
  - Screen 6: Security Settings & Trusted Driver Management (ROI calibration, sensitivity sliders, trusted driver PIN & expiry).
- **Exit Criteria**: App runs smoothly on desktop browser and mobile viewport; responds instantly to real-time events without page reloads.

### Phase 6: System Integration, E2E Testing & Demo Hardening
- **Goal**: Full end-to-end integration, performance tuning, failure mode handling, and demo script validation.
- **Deliverables**:
  - Full flow demonstration script and automated seed runner (`demo_setup.js`).
  - Stress testing of camera disconnect, reconnection, and offline event queueing.
  - Comprehensive documentation, user manual, and architectural diagrams.
- **Exit Criteria**: Flawless live demonstration matching the exam/college presentation workflow from initial armed state to intruder detection, alert notification, and live map tracking.
