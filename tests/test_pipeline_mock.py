import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pose_processing import PoseNormalizer, TemporalSmoother
from src.motion_calculator import MotionCalculator
from src.bvh_exporter import BVHExporter
from src.config import (
    MP_LEFT_HIP, MP_RIGHT_HIP, MP_LEFT_KNEE, MP_RIGHT_KNEE,
    MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_NOSE,
    MP_LEFT_ELBOW, MP_RIGHT_ELBOW, MP_LEFT_WRIST, MP_RIGHT_WRIST
)

def test_pipeline_mock():
    print("Running Mock Pipeline Test...")
    
    # 1. Generate Mock Landmarks (T-Pose)
    # 33 landmarks, 4 channels [x, y, z, vis]
    mock_landmarks = np.zeros((33, 4))
    
    # Define T-Pose positions (Meters approx)
    # Coordinate system: +Y Up, +X Left, +Z Forward (MediaPipe World is different but we normalize)
    # MediaPipe World: +Y Down, +X Right, +Z Target?
    # Actually MP World: Origin at mid-hip. +Y is Down (in image), but World landmarks?
    # MP World: "The magnitude of z uses roughly the same scale as x."
    # Let's just create a set of points that form a text-book T-Pose in OUR target space 
    # (or what the normalizer expects).
    # The normalizer just centers the hips.
    # The calculator expects MP landmark indices.
    
    # Hips (Center 0,0,0)
    mock_landmarks[MP_LEFT_HIP] = [0.1, 0.0, 0.0, 1.0]   # Left
    mock_landmarks[MP_RIGHT_HIP] = [-0.1, 0.0, 0.0, 1.0] # Right
    
    # Legs (Down)
    mock_landmarks[MP_LEFT_KNEE] = [0.1, -0.5, 0.0, 1.0]
    mock_landmarks[MP_RIGHT_KNEE] = [-0.1, -0.5, 0.0, 1.0]
    
    # Spine/Head (Up)
    # MP shoulders
    mock_landmarks[MP_LEFT_SHOULDER] = [0.2, 0.5, 0.0, 1.0]
    mock_landmarks[MP_RIGHT_SHOULDER] = [-0.2, 0.5, 0.0, 1.0]
    mock_landmarks[MP_NOSE] = [0.0, 0.7, 0.0, 1.0] # Head
    
    # Arms (Outwards - T-Pose)
    mock_landmarks[MP_LEFT_ELBOW] = [0.5, 0.5, 0.0, 1.0]  # Left arm out
    mock_landmarks[MP_RIGHT_ELBOW] = [-0.5, 0.5, 0.0, 1.0] # Right arm out
    mock_landmarks[MP_LEFT_WRIST] = [0.8, 0.5, 0.0, 1.0]
    mock_landmarks[MP_RIGHT_WRIST] = [-0.8, 0.5, 0.0, 1.0]
    
    # Create a sequence of 10 frames with slight movement
    frames = []
    for i in range(10):
        frame_lm = mock_landmarks.copy()
        # Add some bobbing or swaying
        frame_lm[:, 1] += np.sin(i * 0.5) * 0.02 # Y-bounce
        frames.append(frame_lm)
        
    # 2. Pipeline Components
    normalizer = PoseNormalizer()
    smoother = TemporalSmoother(window_length=3, polyorder=1) # Small window for few frames
    calculator = MotionCalculator()
    output_path = os.path.join("outputs", "mock_test.bvh")
    exporter = BVHExporter(output_path, fps=30)
    
    # 3. Execution using Main Logic
    smoothed = smoother.smooth_all(frames)
    
    for landmarks in smoothed:
        norm_lm = normalizer.normalize_pose(landmarks)
        rotations, root_pos = calculator.calculate_joint_angles(norm_lm)
        exporter.add_frame(root_pos, rotations)
        
    exporter.export()
    
    # 4. Verify
    if os.path.exists(output_path):
        print("Mock BVH generated successfully.")
        
        # Run Sanity Check
        from check_bvh import check_bvh
        if check_bvh(output_path):
            print("Mock Test PASSED.")
        else:
            print("Mock Test FAILED (NaN check).")
    else:
        print("Mock Test FAILED (File not created).")

if __name__ == "__main__":
    test_pipeline_mock()
