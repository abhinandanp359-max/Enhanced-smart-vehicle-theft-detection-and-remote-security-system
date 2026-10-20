"""
ai_engine/test_engine.py - Automated verification and unit tests for AI Security Engine
"""
import sys
import numpy as np

def run_tests():
    print("[TEST 1/4] Verifying Core Dependencies...")
    import cv2
    import requests
    from ultralytics import YOLO
    from ai_engine.config import DEFAULT_ROI_POLYGON, SUSTAINED_SECONDS
    from ai_engine.state_machine import TheftStateMachine, SystemMode, DetectionState
    from ai_engine.detector import PersonDetector
    from ai_engine.sound_alarm import AlarmSiren
    from ai_engine.backend_client import BackendClient
    print("  -> All core modules imported successfully.")

    print("\n[TEST 2/4] Verifying State Machine & Anti-False-Alarm Logic...")
    sm = TheftStateMachine(sustained_seconds=1.0)
    
    # 1. Clear state
    res = sm.update(person_in_roi=False)
    assert res['state'] == DetectionState.CLEAR, "State should be CLEAR"
    assert not res['trigger_alarm_now'], "Should not alarm on empty seat"

    # 2. Momentary presence (simulate passerby for 0.5s)
    res = sm.update(person_in_roi=True, confidence=0.88)
    assert res['state'] == DetectionState.ACCUMULATING, "State should be ACCUMULATING"
    assert not res['trigger_alarm_now'], "Should not alarm immediately"

    # 3. Person leaves -> false alarm suppressed!
    res = sm.update(person_in_roi=False)
    assert res['state'] == DetectionState.CLEAR, "State should reset to CLEAR when person leaves"
    print("  -> Anti-false-alarm temporal accumulator verified.")

    print("\n[TEST 3/4] Verifying ROI Polygon Geometry...")
    pixel_roi = PersonDetector.get_pixel_roi((720, 1280), DEFAULT_ROI_POLYGON)
    assert len(pixel_roi) == 4, "ROI should have 4 vertices"

    # Test point inside ROI
    inside_detection = {
        'bbox': (500, 300, 700, 600),
        'center': (600, 450),
        'confidence': 0.95
    }
    assert PersonDetector.is_in_roi(inside_detection, pixel_roi), "Center should be in ROI"

    # Test point outside ROI (e.g. at extreme left)
    outside_detection = {
        'bbox': (10, 10, 50, 80),
        'center': (30, 45),
        'confidence': 0.95
    }
    assert not PersonDetector.is_in_roi(outside_detection, pixel_roi), "Point at edge should not be in ROI"
    print("  -> ROI spatial polygon gating verified.")

    print("\n[TEST 4/4] Verifying YOLOv8 Model Initialization & Synthetic Frame...")
    detector = PersonDetector()
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(dummy_frame)
    assert isinstance(detections, list), "Detections should return a list"
    print("  -> YOLOv8 detector verified successfully.")

    print("\n" + "=" * 50)
    print("ALL AI ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    run_tests()
