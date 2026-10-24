"""
ai_engine/sound_alarm.py - High-Decibel Emergency Vehicle Theft Siren
Plays realistic, piercing, continuous alarm siren sound via non-blocking hardware audio.
"""
import os
import sys
import threading
import time
import wave
import numpy as np
from .config import SOUND_ENABLED

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
SIREN_WAV_PATH = os.path.join(MODELS_DIR, "emergency_siren.wav")

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def ensure_siren_audio_file():
    """Generates a piercing, high-intensity multi-harmonic emergency wail siren if missing."""
    if os.path.exists(SIREN_WAV_PATH) and os.path.getsize(SIREN_WAV_PATH) > 10000:
        return

    os.makedirs(MODELS_DIR, exist_ok=True)
    sample_rate = 44100
    duration = 4.0  # 4 second seamless looping siren
    total_samples = int(sample_rate * duration)

    t = np.linspace(0, duration, total_samples, endpoint=False)
    # Sweeping modulation frequency from 600 Hz to 1750 Hz (high acoustic penetration)
    sweep = (np.sin(2 * np.pi * 0.5 * t) + 1.0) / 2.0
    freq = 600 + 1150 * sweep
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate

    # Fundamental + rich harmonics + warble screech
    signal = (
        0.58 * np.sin(phase) +
        0.26 * np.sin(2 * phase) +
        0.16 * np.sin(3 * phase) +
        0.10 * np.sin(4 * phase)
    )
    signal += 0.14 * np.sin(2 * np.pi * 14 * t) * np.sin(phase)
    signal = np.clip(signal, -1.0, 1.0)
    int_signal = (signal * 32000).astype(np.int16)

    with wave.open(SIREN_WAV_PATH, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_signal.tobytes())


class AlarmSiren:
    def __init__(self, enabled=SOUND_ENABLED):
        self.enabled = enabled
        self._playing = False
        ensure_siren_audio_file()

    def start(self):
        """Start the loud emergency siren in non-blocking continuous loop."""
        if not self.enabled or self._playing:
            return

        self._playing = True
        if HAS_WINSOUND and sys.platform.startswith("win"):
            try:
                # SND_ASYNC plays in background; SND_LOOP plays continuously until stopped
                winsound.PlaySound(
                    SIREN_WAV_PATH,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )
            except Exception as e:
                print(f"[Siren] Error starting audio: {e}")
        else:
            # Fallback for non-Windows
            threading.Thread(target=self._terminal_fallback, daemon=True).start()

    def stop(self):
        """Immediately stop the emergency siren."""
        if not self._playing:
            return
        self._playing = False
        if HAS_WINSOUND and sys.platform.startswith("win"):
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    def is_playing(self):
        return self._playing

    def _terminal_fallback(self):
        while self._playing:
            print("\a", end="", flush=True)
            time.sleep(0.4)

