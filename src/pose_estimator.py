"""
pose_estimator.py — MediaPipe Pose Landmarker wrapper (Tasks API, mediapipe >= 0.10).

The legacy `mp.solutions.pose` API was removed in mediapipe 0.10.
This module uses `mediapipe.tasks.python.vision.PoseLandmarker` instead.

World landmarks (z in meters, origin at hips) map 1-to-1 to the same 33
landmark indices as before, so the rest of the pipeline is unchanged.
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

# Default model path — downloaded once into the project's models/ folder
_DEFAULT_MODEL = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),   # project root
    "models",
    "pose_landmarker_full.task",
)


class PoseEstimator:
    """
    Wraps MediaPipe PoseLandmarker (Tasks API).

    Args:
        model_path:               Path to .task model file.
        min_detection_confidence: Minimum pose detection confidence.
        min_tracking_confidence:  Minimum pose tracking confidence.
    """

    def __init__(
        self,
        model_path: str = _DEFAULT_MODEL,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"MediaPipe model not found at: {model_path}\n"
                "Download it with:\n"
                "  Invoke-WebRequest -Uri https://storage.googleapis.com/mediapipe-models/"
                "pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
                " -OutFile models/pose_landmarker_full.task"
            )

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,          # VIDEO mode for sequential frames
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        self._frame_ts_ms = 0          # monotonically increasing timestamp
        self._frame_interval_ms = 33   # default ~30 fps; updated per-video in pipeline

    def set_fps(self, fps: float):
        """Call this once with the video FPS so timestamps are accurate."""
        self._frame_interval_ms = max(1, int(1000.0 / fps))

    def process_frame(self, frame: np.ndarray):
        """
        Process one BGR frame and return the raw PoseLandmarkerResult.

        Args:
            frame: BGR numpy array from OpenCV.

        Returns:
            result: PoseLandmarkerResult (may have empty pose_landmarks list).
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self._landmarker.detect_for_video(mp_image, self._frame_ts_ms)
        self._frame_ts_ms += self._frame_interval_ms
        return result

    def extract_world_landmarks(self, result) -> np.ndarray | None:
        """
        Extract world landmarks as a (33, 4) array[x, y, z, visibility].
        World landmarks are in meters, origin at the mid-hip.
        """
        if not result.pose_world_landmarks:
            return None

        lm_list = result.pose_world_landmarks[0]   # first (only) pose
        arr = np.zeros((33, 4), dtype=np.float32)
        for i, lm in enumerate(lm_list):
            arr[i, 0] = lm.x
            arr[i, 1] = -lm.y   # FLIPPED: Make +Y point towards the Sky
            arr[i, 2] = -lm.z   # FLIPPED: Make +Z point towards the Camera
            arr[i, 3] = getattr(lm, "visibility", 1.0) or 1.0
        return arr

    def extract_landmarks(self, result) -> np.ndarray | None:
        """
        Extract normalised image-space landmarks as a (33, 4) array.
        (x, y are in [0,1] image coords; z is depth relative to hips)
        """
        if not result.pose_landmarks:
            return None

        lm_list = result.pose_landmarks[0]
        arr = np.zeros((33, 4), dtype=np.float32)
        for i, lm in enumerate(lm_list):
            arr[i, 0] = lm.x
            arr[i, 1] = lm.y
            arr[i, 2] = lm.z
            arr[i, 3] = getattr(lm, "visibility", 1.0) or 1.0
        return arr

    def draw_landmarks(self, frame: np.ndarray, result) -> np.ndarray:
        """Draw pose landmarks onto a copy of the frame (for visualisation)."""
        annotated = frame.copy()
        if not result.pose_landmarks:
            return annotated

        # Manual drawing — mp.solutions.drawing_utils is not available in 0.10+
        h, w = frame.shape[:2]
        lm_list = result.pose_landmarks[0]

        # Draw joints
        for lm in lm_list:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(annotated, (cx, cy), 4, (0, 255, 120), -1)

        return annotated

    def close(self):
        """Release the underlying landmarker resources."""
        self._landmarker.close()
