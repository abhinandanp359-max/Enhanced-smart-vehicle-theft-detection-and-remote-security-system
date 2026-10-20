"""
ai_engine/state_machine.py - Multi-factor Theft State Machine with Temporal Accumulator
Prevents false alarms by requiring continuous occupancy in the Driver-Seat ROI for T seconds.
"""
import time
from .config import SUSTAINED_SECONDS, ALARM_COOLDOWN_SECONDS


class SystemMode:
    DISARMED = "DISARMED"
    ARMED = "ARMED"


class DetectionState:
    CLEAR = "CLEAR"
    AUTHORIZED_DRIVER = "AUTHORIZED_DRIVER"
    ACCUMULATING = "ACCUMULATING"
    ALARM_ACTIVE = "ALARM_ACTIVE"
    COOLDOWN = "COOLDOWN"


class TheftStateMachine:
    def __init__(self, sustained_seconds=SUSTAINED_SECONDS, cooldown_seconds=ALARM_COOLDOWN_SECONDS):
        self.sustained_seconds = sustained_seconds
        self.cooldown_seconds = cooldown_seconds

        self.system_mode = SystemMode.ARMED  # Default to ARMED for testing
        self.detection_state = DetectionState.CLEAR

        self.occupancy_start_time = None
        self.last_alarm_time = 0
        self.highest_confidence = 0.0

    def arm(self):
        """Arm the security system."""
        self.system_mode = SystemMode.ARMED
        self.reset_detection()
        print("[State Machine] System ARMED.")

    def disarm(self):
        """Disarm the security system."""
        self.system_mode = SystemMode.DISARMED
        self.reset_detection()
        print("[State Machine] System DISARMED.")

    def reset_detection(self):
        """Resets the detection accumulator."""
        self.detection_state = DetectionState.CLEAR
        self.occupancy_start_time = None
        self.highest_confidence = 0.0

    def update(self, person_in_roi, is_authorized=False, driver_name="Intruder", confidence=0.0):
        """
        Evaluate current frame with driver authorization verification.
        Returns a dict with state, authorization, elapsed timer, and alarm trigger.
        """
        now = time.time()
        trigger_alarm = False
        elapsed = 0.0

        # If system is DISARMED, do not accumulate or alarm
        if self.system_mode == SystemMode.DISARMED:
            self.reset_detection()
            return {
                'state': DetectionState.CLEAR,
                'mode': self.system_mode,
                'is_authorized': is_authorized,
                'driver_name': driver_name,
                'elapsed': 0.0,
                'threshold': self.sustained_seconds,
                'trigger_alarm_now': False
            }

        # Check if in cooldown period after a previous alarm
        # PRIORITY 1: If the Authorized Owner is recognized, immediately override any alarm/cooldown!
        if person_in_roi and is_authorized:
            self.detection_state = DetectionState.AUTHORIZED_DRIVER
            self.occupancy_start_time = None
            return {
                'state': DetectionState.AUTHORIZED_DRIVER,
                'mode': self.system_mode,
                'is_authorized': True,
                'driver_name': driver_name,
                'elapsed': 0.0,
                'threshold': self.sustained_seconds,
                'trigger_alarm_now': False,
                'highest_confidence': self.highest_confidence
            }

        # PRIORITY 2: Check if in cooldown period after a previous alarm (intruder mode)
        if self.detection_state == DetectionState.COOLDOWN:
            if now - self.last_alarm_time < self.cooldown_seconds:
                return {
                    'state': DetectionState.COOLDOWN,
                    'mode': self.system_mode,
                    'is_authorized': is_authorized,
                    'driver_name': driver_name,
                    'elapsed': now - self.last_alarm_time,
                    'threshold': self.cooldown_seconds,
                    'trigger_alarm_now': False
                }
            else:
                self.reset_detection()

        # PRIORITY 3: Unauthorized Occupant in Driver Seat (Accumulate toward alarm)
        if person_in_roi:
            self.highest_confidence = max(self.highest_confidence, confidence)

            if self.occupancy_start_time is None:
                self.occupancy_start_time = now
                self.detection_state = DetectionState.ACCUMULATING

            elapsed = now - self.occupancy_start_time

            # Has the unauthorized person remained in the driver seat for >= sustained_seconds?
            if elapsed >= self.sustained_seconds and self.detection_state != DetectionState.ALARM_ACTIVE:
                self.detection_state = DetectionState.ALARM_ACTIVE
                self.last_alarm_time = now
                trigger_alarm = True
        else:
            # Person left the ROI before threshold -> Reset counter (Prevents false alarms!)
            if self.detection_state in [DetectionState.ACCUMULATING, DetectionState.AUTHORIZED_DRIVER]:
                self.reset_detection()
            elif self.detection_state == DetectionState.ALARM_ACTIVE:
                # Intruder fled after alarm
                self.detection_state = DetectionState.COOLDOWN

        return {
            'state': self.detection_state,
            'mode': self.system_mode,
            'is_authorized': is_authorized,
            'driver_name': driver_name,
            'elapsed': elapsed,
            'threshold': self.sustained_seconds,
            'trigger_alarm_now': trigger_alarm,
            'highest_confidence': self.highest_confidence
        }
