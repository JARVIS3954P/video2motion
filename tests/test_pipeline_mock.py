"""
test_pipeline_mock.py — End-to-end pipeline test using synthetic T-Pose landmarks.

Run from the project root:
    python -m pytest tests/test_pipeline_mock.py -v
or
    python tests/test_pipeline_mock.py
"""

import sys
import os
import math
import numpy as np

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.video_motion.core.pose_processing import PoseNormalizer, TemporalSmoother
from src.video_motion.core.motion_calculator import MotionCalculator
from src.video_motion.io.bvh_exporter import BVHExporter
from src.video_motion.config import (
    MP_LEFT_HIP, MP_RIGHT_HIP,
    MP_LEFT_KNEE, MP_RIGHT_KNEE,
    MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER,
    MP_NOSE,
    MP_LEFT_ELBOW, MP_RIGHT_ELBOW,
    MP_LEFT_WRIST, MP_RIGHT_WRIST,
    MP_LEFT_ANKLE, MP_RIGHT_ANKLE,
)
from tests.check_bvh import check_bvh

OUTPUT_PATH = os.path.join(r"C:\dev\data\video-motion-generation-outputs", "mock_test.bvh")
N_FRAMES = 20  # enough for the smoother window


def _make_t_pose_landmarks() -> np.ndarray:
    """Return a 33×4 landmark array in a T-Pose configuration."""
    lm = np.zeros((33, 4))
    lm[:, 3] = 1.0  # all visible

    # Hips (origin)
    lm[MP_LEFT_HIP]  = [0.1, 0.0, 0.0, 1.0]
    lm[MP_RIGHT_HIP] = [-0.1, 0.0, 0.0, 1.0]

    # Legs (down)
    lm[MP_LEFT_KNEE]   = [0.1, -0.45, 0.0, 1.0]
    lm[MP_RIGHT_KNEE]  = [-0.1, -0.45, 0.0, 1.0]
    lm[MP_LEFT_ANKLE]  = [0.1, -0.90, 0.0, 1.0]
    lm[MP_RIGHT_ANKLE] = [-0.1, -0.90, 0.0, 1.0]

    # Shoulders (up + out)
    lm[MP_LEFT_SHOULDER]  = [0.22, 0.55, 0.0, 1.0]
    lm[MP_RIGHT_SHOULDER] = [-0.22, 0.55, 0.0, 1.0]

    # Arms (T-pose — horizontal)
    lm[MP_LEFT_ELBOW]  = [0.55, 0.55, 0.0, 1.0]
    lm[MP_RIGHT_ELBOW] = [-0.55, 0.55, 0.0, 1.0]
    lm[MP_LEFT_WRIST]  = [0.85, 0.55, 0.0, 1.0]
    lm[MP_RIGHT_WRIST] = [-0.85, 0.55, 0.0, 1.0]

    # Head
    lm[MP_NOSE] = [0.0, 0.72, 0.0, 1.0]

    return lm


def test_pipeline_mock():
    print("\n== Mock Pipeline Test =======================================")
    os.makedirs(r"C:\dev\data\video-motion-generation-outputs", exist_ok=True)

    # 1. Build synthetic frame sequence
    base_lm = _make_t_pose_landmarks()
    frames = []
    for i in range(N_FRAMES):
        frame = base_lm.copy()
        # Add gentle Y-bobbing and arm swing to create non-trivial motion
        t = i / N_FRAMES * 2 * math.pi
        frame[:, 1] += math.sin(t) * 0.02          # body bob
        frame[MP_LEFT_ELBOW, 1]  += math.sin(t) * 0.05  # left elbow swing
        frame[MP_RIGHT_ELBOW, 1] -= math.sin(t) * 0.05  # right elbow swing
        frames.append(frame)

    # 2. Smoother
    smoother = TemporalSmoother(window_length=5, polyorder=2)
    smoothed = smoother.smooth_all(frames)
    assert smoothed.shape == (N_FRAMES, 33, 4), (
        f"Expected shape ({N_FRAMES}, 33, 4), got {smoothed.shape}"
    )
    print(f"  [OK] Smoother returned shape {smoothed.shape}")

    # 3. Normalizer + calculator + exporter
    normalizer = PoseNormalizer()
    calculator = MotionCalculator()
    exporter = BVHExporter(output_path=OUTPUT_PATH, fps=30)

    for lm in smoothed:
        norm_lm = normalizer.normalize_pose(lm)
        assert norm_lm is not None, "Normalizer returned None"
        rotations, root_pos = calculator.calculate_joint_angles(norm_lm)
        assert isinstance(rotations, dict), "Rotations must be a dict"
        assert len(rotations) > 0, "Rotations dict is empty"
        exporter.add_frame(root_pos, rotations)

    assert len(exporter.frames) == N_FRAMES, (
        f"Expected {N_FRAMES} frames in exporter, got {len(exporter.frames)}"
    )
    print(f"  [OK] Exporter collected {N_FRAMES} frames")

    # 4. Write to disk
    exporter.export()
    assert os.path.exists(OUTPUT_PATH), "BVH file was not created"
    size = os.path.getsize(OUTPUT_PATH)
    assert size > 0, "BVH file is empty"
    print(f"  [OK] BVH file written ({size} bytes)")

    # 5. In-memory string matches disk content
    bvh_str = exporter.get_bvh_string()
    assert "HIERARCHY" in bvh_str, "HIERARCHY missing from BVH string"
    assert "MOTION" in bvh_str, "MOTION missing from BVH string"
    print("  [OK] get_bvh_string() contains HIERARCHY and MOTION blocks")

    # 6. Full file validation
    passed = check_bvh(OUTPUT_PATH)
    assert passed, "check_bvh() reported failures (see output above)"

    print("== Mock Pipeline Test PASSED\n")
    return True


if __name__ == "__main__":
    ok = test_pipeline_mock()
    sys.exit(0 if ok else 1)
