# SPEC.md — Project Specification: Smart Vehicle Theft Detection & Remote Security System

> **Status**: `FINALIZED`

## 1. Vision
An AI-powered, IoT-capable in-vehicle security system that monitors the driver cabin when armed, accurately detects unauthorized occupancy and suspicious access using computer vision (YOLOv8 + OpenCV), suppresses false alarms via multi-factor temporal and spatial verification, triggers local audible deterrents, immediately transmits visual evidence and telemetry to a cloud/backend server, and empowers the owner with remote mobile control (Arm/Disarm, Trusted Driver mode, incident review, and live GPS tracking).

## 2. Core Goals & Success Criteria
1. **Accurate Theft Detection**: Differentiate between an empty driver area and an unauthorized occupant sitting in the driver's seat using YOLOv8 person detection constrained to a configurable Driver-Seat Region of Interest (ROI) with temporal persistence (minimum occupancy duration $T$ seconds) to avoid false positives.
2. **Immediate Evidence Capture & Deterrent**: Automatically record an annotated high-resolution snapshot and short video buffer clip upon confirmed theft, while triggering an emergency audible siren/alarm locally.
3. **Remote Owner Control & Real-Time Sync**: Deliver sub-second alert delivery and remote state management (Security ON / Security OFF / Trusted Driver Mode / Disarm Alarm) via a responsive mobile-friendly dashboard connected through Socket.io.
4. **Live Post-Theft Tracking**: Seamlessly switch to real-time GPS telemetry streaming (simulated for prototype, hardware-ready) displaying the vehicle's simulated trajectory on an interactive map.
5. **Auditable Security History**: Store chronological security incidents with timestamp, location, snapshot, video link, and acknowledgement status in MongoDB.

## 3. Scope Boundaries & Constraints
- **Prototype Scope**: Safe indoor demonstration using a PC/laptop, USB/integrated webcam, and local speakers/buzzer.
- **Hardware Agnostic**: Software architecture must cleanly abstract Camera, GPS, and Alarm behind provider interfaces so real hardware (Raspberry Pi / Jetson, NEO-6M GPS, relay immobilizer) can replace mock providers without rewriting core logic.
- **False Alarm Prevention**: "Person detected $\neq$ Thief". Triggering requires: `Security Mode == ARMED` AND `Detection in Driver Seat ROI` AND `Occupancy Duration >= Threshold` AND `Not in Trusted Driver Window`.

---
*Created: 2026-10-05*
