"""
ai_engine/sound_alarm.py - Local audible alarm siren generator
Runs in a background thread so the camera inference loop never stutters.
"""
import sys
import threading
import time
from .config import SOUND_ENABLED

# Native Windows sound support
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class AlarmSiren:
    def __init__(self, enabled=SOUND_ENABLED):
        self.enabled = enabled
        self._playing = False
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the siren sound in a non-blocking background thread."""
        if not self.enabled or self._playing:
            return

        self._playing = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._siren_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Immediately stop the siren."""
        self._playing = False
        self._stop_event.set()

    def is_playing(self):
        return self._playing

    def _siren_loop(self):
        """Alternating two-tone emergency siren sound."""
        while not self._stop_event.is_set():
            if HAS_WINSOUND and sys.platform.startswith("win"):
                try:
                    # High tone
                    winsound.Beep(1300, 250)
                    if self._stop_event.is_set():
                        break
                    # Low tone
                    winsound.Beep(850, 250)
                except Exception:
                    time.sleep(0.5)
            else:
                # Terminal bell fallback on other platforms
                print("\a", end="", flush=True)
                time.sleep(0.5)
