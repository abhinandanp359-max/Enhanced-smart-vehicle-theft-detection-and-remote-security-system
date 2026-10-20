"""
ai_engine/hardware_controller.py - ESP32 Hardware Deterrent Controller
Communicates via USB Serial with ESP32 to trigger:
  1. Buzzer emergency alarm sound.
  2. Red LED warning light.
  3. Green LED access granted confirmation.
Gracefully operates in simulation mode if ESP32 is not plugged in.
"""
import glob
import os
import sys
import threading
import time

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class ESP32Controller:
    def __init__(self, port=None, baudrate=115200):
        self.port = port or os.getenv("ESP32_PORT", "AUTO")
        self.baudrate = baudrate
        self.connection = None
        self.is_connected = False
        self._lock = threading.Lock()

        self.connect()

    def find_esp32_port(self):
        """Scans system COM ports to find connected ESP32 / USB-Serial device."""
        if not HAS_SERIAL:
            return None

        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = p.description.lower()
            # Common USB-Serial chipsets used by ESP32 (CP210x, CH340, FTDI, USB-Serial)
            if any(k in desc for k in ["cp210", "ch340", "ch341", "usb-serial", "ftdi", "esp32"]):
                print(f"[Hardware] Detected ESP32 on port: {p.device} ({p.description})")
                return p.device

        # If user specified a direct port like COM3, use it
        if self.port and self.port != "AUTO":
            return self.port

        return None

    def connect(self):
        """Opens serial connection to ESP32."""
        if not HAS_SERIAL:
            print("[Hardware] pyserial not available. Operating in simulation mode.")
            return False

        target_port = self.find_esp32_port() if self.port == "AUTO" else self.port

        if not target_port:
            print("[Hardware] (Notice) ESP32 USB not detected. Hardware simulation mode active (PC speaker + screen indicator).")
            return False

        try:
            self.connection = serial.Serial(target_port, self.baudrate, timeout=1)
            time.sleep(1.5)  # Allow ESP32 reboot delay after connection
            self.is_connected = True
            print(f"[Hardware] >>> ESP32 Connected Successfully on {target_port}! Buzzer & LED Armed. <<<")
            return True
        except Exception as e:
            print(f"[Hardware] Could not connect to {target_port}: {e}")
            self.is_connected = False
            return False

    def send_command(self, cmd_str):
        """Thread-safe command dispatcher to ESP32."""
        with self._lock:
            if not self.is_connected or not self.connection:
                return

            try:
                line = (cmd_str.strip() + "\n").encode("utf-8")
                self.connection.write(line)
                self.connection.flush()
            except Exception as e:
                print(f"[Hardware] Serial communication error: {e}")
                self.is_connected = False

    def trigger_alarm(self):
        """Triggers Buzzer and Red LED on ESP32."""
        print("[Hardware] >>> ESP32: SENDING 'ALARM_ON' (Buzzer Sound + Red LED Active) <<<")
        self.send_command("ALARM_ON")

    def silence_alarm(self):
        """Silences Buzzer and turns off Red LED on ESP32."""
        self.send_command("ALARM_OFF")

    def grant_access(self):
        """Flashes Green LED on ESP32 (Owner Verified)."""
        self.send_command("AUTH_OK")

    def close(self):
        """Closes serial connection safely."""
        self.silence_alarm()
        if self.connection and self.connection.is_open:
            try:
                self.connection.close()
            except Exception:
                pass
        self.is_connected = False
