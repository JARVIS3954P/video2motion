"""
pipeline_runner.py — Orchestrates the full Video → BVH pipeline.

Usage:
    runner = PipelineRunner()
    bvh_content = runner.run(
        video_path="input.mp4",
        output_path="outputs/out.bvh",          # optional, pass None to skip disk write
        progress_callback=lambda step, frac: ... # optional
    )
"""

import os

from .video_loader import VideoLoader
from .pose_estimator import PoseEstimator
from .pose_processing import PoseNormalizer, TemporalSmoother
from .motion_calculator import MotionCalculator
from .bvh_exporter import BVHExporter


class PipelineRunner:
    """
    Encapsulates the full motion-extraction pipeline.

    Stages:
        1. Frame extraction + pose estimation  (MediaPipe)
        2. Temporal smoothing                  (Savitzky-Golay)
        3. Joint-angle calculation + BVH export
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
        smooth_window: int = 11,
        smooth_polyorder: int = 3,
    ):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.smooth_window = smooth_window
        self.smooth_polyorder = smooth_polyorder

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(
        self,
        video_path: str,
        output_path: str | None = None,
        progress_callback=None,
    ) -> str:
        """
        Run the full pipeline.

        Args:
            video_path:        Path to input video.
            output_path:       Path to write the BVH file.  Pass None to
                               skip writing and only return the string.
            progress_callback: Optional callable(step: str, fraction: float).
                               step    — human-readable stage label
                               fraction — 0.0 … 1.0

        Returns:
            bvh_content (str): The complete BVH file as a string.

        Raises:
            FileNotFoundError, IOError, RuntimeError  with descriptive messages.
        """
        self._cb = progress_callback or (lambda s, f: None)

        # ── Stage 1: Pose Extraction ───────────────────────────────────
        self._cb("Initialising pipeline…", 0.0)

        try:
            loader = VideoLoader(video_path)
        except (FileNotFoundError, IOError) as e:
            raise RuntimeError(f"Could not open video: {e}") from e

        estimator = PoseEstimator(
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        estimator.set_fps(loader.fps)   # accurate per-frame timestamps for VIDEO mode

        total_frames = loader.frame_count or 1
        all_landmarks = []
        frame_idx = 0

        self._cb("Step 1/3 — Extracting pose landmarks…", 0.0)

        for frame in loader:
            results = estimator.process_frame(frame)
            landmarks = estimator.extract_world_landmarks(results)

            if landmarks is not None:
                all_landmarks.append(landmarks)
            elif all_landmarks:
                # Repeat last known good frame
                all_landmarks.append(all_landmarks[-1])
            # Skip leading None frames (person not yet in view)

            frame_idx += 1
            if frame_idx % 5 == 0:
                self._cb(
                    f"Step 1/3 — Extracting pose landmarks… ({frame_idx}/{total_frames} frames)",
                    min(frame_idx / total_frames, 1.0) * 0.50,
                )

        loader.release()
        estimator.close()   # release native MediaPipe resources

        all_landmarks = [lm for lm in all_landmarks if lm is not None]

        if not all_landmarks:
            raise RuntimeError(
                "No human pose was detected in the video. "
                "Ensure the video contains a clearly visible person."
            )

        # ── Stage 2: Temporal Smoothing ────────────────────────────────
        self._cb("Step 2/3 — Smoothing motion data…", 0.50)

        window = min(self.smooth_window, len(all_landmarks) - 1)
        # window must be odd and > polyorder
        if window % 2 == 0:
            window -= 1
        window = max(window, self.smooth_polyorder + 1)
        if window % 2 == 0:
            window += 1

        smoother = TemporalSmoother(
            window_length=window,
            polyorder=min(self.smooth_polyorder, window - 1),
        )
        smoothed_landmarks = smoother.smooth_all(all_landmarks)
        self._cb("Step 2/3 — Smoothing motion data… done", 0.60)

        # ── Stage 3: Joint Angles & BVH Export ────────────────────────
        self._cb("Step 3/3 — Calculating joint angles…", 0.60)

        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        normalizer = PoseNormalizer()
        calculator = MotionCalculator()
        exporter = BVHExporter(output_path=output_path, fps=loader.fps)

        n_frames = len(smoothed_landmarks)
        for i, landmarks in enumerate(smoothed_landmarks):
            norm_lm = normalizer.normalize_pose(landmarks)
            rotations, root_pos = calculator.calculate_joint_angles(norm_lm)
            exporter.add_frame(root_pos, rotations)

            if i % 10 == 0:
                self._cb(
                    f"Step 3/3 — Calculating joint angles… ({i}/{n_frames} frames)",
                    0.60 + (i / n_frames) * 0.39,
                )

        # Write file if requested
        if output_path:
            exporter.export()

        bvh_content = exporter.get_bvh_string()
        self._cb("Done!", 1.0)
        return bvh_content
