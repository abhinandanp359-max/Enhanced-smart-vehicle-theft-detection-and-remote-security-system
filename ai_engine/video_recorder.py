"""
ai_engine/video_recorder.py - Circular Buffer & Incident Video Clip Recorder
Maintains rolling pre-event video buffer and saves short MP4 clips of the intrusion.
Runs in a background thread so video streaming never blocks or stutters.
"""
import collections
import os
import threading
import time
import cv2
from .config import EVIDENCE_DIR, VEHICLE_ID


class VideoEvidenceRecorder:
    def __init__(self, pre_event_seconds=3.0, fps=20, evidence_dir=EVIDENCE_DIR, vehicle_id=VEHICLE_ID):
        self.fps = fps
        self.max_buffer_len = int(pre_event_seconds * fps)
        self.buffer = collections.deque(maxlen=self.max_buffer_len)
        self.evidence_dir = evidence_dir
        self.vehicle_id = vehicle_id
        os.makedirs(self.evidence_dir, exist_ok=True)

        self._recording = False
        self._post_frames_needed = 0
        self._active_clip_frames = []
        self._on_complete_callback = None

    def add_frame(self, frame):
        """Adds frame to circular buffer or active recording clip."""
        # Always store in circular buffer for pre-event footage
        self.buffer.append(frame.copy())

        # If currently recording post-event footage
        if self._recording:
            self._active_clip_frames.append(frame.copy())
            if len(self._active_clip_frames) >= self._post_frames_needed:
                self._recording = False
                clip_frames = list(self._active_clip_frames)
                self._active_clip_frames = []
                # Save clip in background thread
                threading.Thread(
                    target=self._save_clip_worker,
                    args=(clip_frames, self._on_complete_callback),
                    daemon=True
                ).start()

    def record_incident_clip(self, post_event_seconds=2.5, on_complete=None):
        """
        Starts recording an incident video clip.
        Combines the pre-event buffer + post-event seconds into a clean MP4 file.
        """
        if self._recording:
            return None

        # Start with all frames captured right before the alarm
        self._active_clip_frames = list(self.buffer)
        self._post_frames_needed = len(self._active_clip_frames) + int(post_event_seconds * self.fps)
        self._recording = True
        self._on_complete_callback = on_complete

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_filename = f"theft_intruder_{self.vehicle_id}_{timestamp}.mp4"
        video_filepath = os.path.join(self.evidence_dir, video_filename)
        return video_filepath

    def _save_clip_worker(self, frames, callback):
        """Worker thread to encode and save frames into an MP4 video file."""
        if not frames:
            return

        h, w = frames[0].shape[:2]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_filename = f"theft_intruder_{self.vehicle_id}_{timestamp}.mp4"
        video_filepath = os.path.join(self.evidence_dir, video_filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_filepath, fourcc, self.fps, (w, h))

        for f in frames:
            out.write(f)
        out.release()

        print(f"[Video Recorder] >>> Incident video clip recorded ({len(frames)} frames): {video_filepath} <<<")
        if callback:
            callback(video_filepath)
