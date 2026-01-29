import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pose_processing import PoseNormalizer, TemporalSmoother
from src.motion_calculator import MotionCalculator
from src.bvh_exporter import BVHExporter
from src.config import MP_LEFT_HIP, MP_RIGHT_HIP

def test_pipeline_mock():
    print("Running Mock Pipeline Test...")
    
    # 1. Generate Mock Landmarks (T-Pose-ish)
    # 33 landmarks, 4 channels
    mock_landmarks = np.zeros((33, 4))
    
    # Set hips roughly apart
    mock_landmarks[MP_LEFT_HIP] = [0.1, 0.0, 0.0, 1.0]
    mock_landmarks[MP_RIGHT_HIP] = [-0.1, 0.0, 0.0, 1.0]
    
    # Create a sequence of 10 frames with slight movement
    frames = []
    for i in range(10):
        frame_lm = mock_landmarks.copy()
        frame_lm[:, 0] += i * 0.01 # Move in X
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
