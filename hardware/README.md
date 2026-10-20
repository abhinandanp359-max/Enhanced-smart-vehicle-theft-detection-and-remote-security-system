# ESP32 Hardware Deterrent System — Wiring & Setup Guide

This guide describes how to connect the **ESP32**, **Buzzer**, and **LEDs** to the Smart Vehicle Security AI Engine.

---

## 1. Hardware Required
1. **ESP32 Development Board** (NodeMCU-32S, ESP32-WROOM-32, etc.)
2. **Active Buzzer** (5V or 3.3V) or Piezo Buzzer
3. **Red LED** (Theft Intrusion Alert)
4. **Green LED** (Optional: Owner Access Granted confirmation)
5. **2x 220Ω Resistors** (for LEDs)
6. **Breadboard & Jumper Wires**
7. **Micro-USB / USB-C Cable** (connecting ESP32 to Laptop)

---

## 2. Circuit Diagram & Wiring Table

```
           ┌──────────────────────────────────────────────┐
           │                   ESP32                      │
           │                                              │
           │  GPIO 18 ────────── (+) Buzzer Terminal      │
           │                                              │
           │  GPIO 19 ──[220Ω]── (+) Red LED (Long Leg)   │
           │                                              │
           │  GPIO 21 ──[220Ω]── (+) Green LED (Long Leg) │
           │                                              │
           │  GND ────────────── (-) Buzzer, Red & Green  │
           │                         LED Short Legs       │
           └──────────────────────────────────────────────┘
```

| ESP32 Pin | Component Pin | Notes |
|:---|:---|:---|
| **GPIO 18** | **Buzzer (+)** (Red wire / Long leg) | Active Buzzer trigger |
| **GPIO 19** | **Red LED (+)** (via 220Ω resistor) | Theft Alarm indicator |
| **GPIO 21** | **Green LED (+)** (via 220Ω resistor) | Authorized Owner indicator |
| **GND** | **Buzzer (-)** & **Both LEDs (-)** (Flat edge / Short legs) | Common Ground |

---

## 3. How to Flash the ESP32 (Arduino IDE)

1. Open **Arduino IDE**.
2. Go to **Tools $\rightarrow$ Board** and select **`ESP32 Dev Module`** (or your specific ESP32 board).
3. Connect your ESP32 to your PC via USB cable.
4. Go to **Tools $\rightarrow$ Port** and select your COM Port (e.g. `COM3` or `COM4`).
5. Open the firmware sketch:
   `hardware/esp32_firmware/esp32_firmware.ino`
6. Click **Upload** (Arrow icon).
7. Once uploaded, the ESP32 will emit a short chirp and blink its LED, confirming it is ready!

---

## 4. How It Works with Python AI Engine

1. Connect the ESP32 via USB cable to your laptop.
2. Run the main system:
   ```powershell
   python -m ai_engine.main
   ```
3. The Python program automatically detects the connected ESP32 COM port and connects at `115200` baud.
4. **Behavior**:
   - **Authorized Owner Detected**:
     - Sends `AUTH_OK` $\rightarrow$ Flashes **Green LED**, Buzzer stays **Silent**.
   - **Unauthorized Intruder Detected ($\ge 3$s)**:
     - Sends `ALARM_ON` $\rightarrow$ Triggers **Buzzer Siren Sound** + **Flashing Red LED**!
     - Captures incident photo (`.jpg`) and video (`.mp4`).
   - **Owner Arrives / Alarm Silenced**:
     - Sends `ALARM_OFF` $\rightarrow$ Instantly turns **OFF** Buzzer and Red LED.

*(Note: If the ESP32 is unplugged, the Python system automatically runs in simulation mode using your PC speaker and on-screen HUD without crashing).*
