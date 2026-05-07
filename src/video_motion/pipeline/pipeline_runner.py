import os

from ..core.motion_calculator import MotionCalculator
from ..core.pose_estimator import PoseEstimator
from ..core.pose_processing import PoseNormalizer, TemporalSmoother
from ..io.bvh_exporter import BVHExporter
from ..io.video_loader import VideoLoader


class PipelineRunner:
    """
    Orchestrates Video -> MediaPipe landmarks -> smoothed rotations -> BVH.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
        smooth_window: int = 9,
        smooth_polyorder: int = 2,
        keep_root_motion: bool = True,
    ):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.smooth_window = smooth_window
        self.smooth_polyorder = smooth_polyorder
        self.keep_root_motion = keep_root_motion

    def run(
        self,
        video_path: str,
        output_path: str | None = None,
        progress_callback=None,
    ) -> str:
        self._cb = progress_callback or (lambda s, f: None)
        self._cb("Initialising pipeline...", 0.0)

        try:
            loader = VideoLoader(video_path)
        except (FileNotFoundError, IOError) as e:
            raise RuntimeError(f"Could not open video: {e}") from e

        estimator = PoseEstimator(
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )
        estimator.set_fps(loader.fps)

        total_frames = loader.frame_count or 1
        all_landmarks = []

        self._cb("Step 1/3 - Extracting pose landmarks...", 0.0)
        for frame_idx, frame in enumerate(loader, start=1):
            results = estimator.process_frame(frame)
            all_landmarks.append(estimator.extract_world_landmarks(results))

            if frame_idx % 5 == 0:
                self._cb(
                    f"Step 1/3 - Extracting pose landmarks... ({frame_idx}/{total_frames} frames)",
                    min(frame_idx / total_frames, 1.0) * 0.50,
                )

        loader.release()
        estimator.close()

        if not any(lm is not None for lm in all_landmarks):
            raise RuntimeError(
                "No human pose was detected in the video. "
                "Ensure the video contains a clearly visible person."
            )

        self._cb("Step 2/3 - Interpolating and smoothing motion data...", 0.50)
        smoother = TemporalSmoother(
            window_length=self.smooth_window,
            polyorder=self.smooth_polyorder,
        )
        smoothed_landmarks = smoother.smooth_all(all_landmarks)
        self._cb("Step 2/3 - Smoothing motion data... done", 0.60)

        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        normalizer = PoseNormalizer()
        calculator = MotionCalculator()
        exporter = BVHExporter(output_path=output_path, fps=loader.fps)
        n_frames = len(smoothed_landmarks)

        first_frame_norm = normalizer.normalize_pose(smoothed_landmarks[0])
        calculator.calibrate(first_frame_norm)

        all_rotations = []
        all_root_pos = []
        first_root = normalizer.hip_center(smoothed_landmarks[0])

        self._cb("Step 3/3 - Calculating joint angles...", 0.60)
        for i, landmarks in enumerate(smoothed_landmarks):
            root_pos = normalizer.hip_center(landmarks) - first_root
            if not self.keep_root_motion:
                root_pos[:] = 0.0

            norm_lm = normalizer.normalize_pose(landmarks)
            rotations, root_pos = calculator.calculate_joint_angles(norm_lm, root_position=root_pos)
            all_rotations.append(rotations)
            all_root_pos.append(root_pos)

            if i % 10 == 0:
                self._cb(
                    f"Step 3/3 - Calculating joint angles... ({i}/{n_frames} frames)",
                    0.60 + (i / n_frames) * 0.35,
                )

        self._cb("Finalizing and smoothing joint angles...", 0.95)
        all_rotations = smoother.smooth_rotations(all_rotations)
        all_root_pos = smoother.smooth_vectors(all_root_pos)

        for i in range(n_frames):
            exporter.add_frame(all_root_pos[i], all_rotations[i])

        if output_path:
            exporter.export()

        bvh_content = exporter.get_bvh_string()
        self._cb("Done!", 1.0)
        return bvh_content
