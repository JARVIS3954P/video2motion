import argparse
import os
import cv2
from src.video_loader import VideoLoader
from src.pose_estimator import PoseEstimator
from src.pose_processing import PoseNormalizer, TemporalSmoother
from src.motion_calculator import MotionCalculator
from src.bvh_exporter import BVHExporter

def main():
    parser = argparse.ArgumentParser(description="One-Person Motion Extraction System")
    parser.add_argument("input_video", help="Path to input video file")
    parser.add_argument("--output", "-o", help="Path to output BVH file", default=None)
    parser.add_argument("--visualize", "-v", action="store_true", help="Show processing window")
    args = parser.parse_args()

    input_path = args.input_video
    if args.output:
        output_path = args.output
    else:
        # Default output name based on input
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join("outputs", f"{base_name}.bvh")
        
    print(f"Processing: {input_path}")
    print(f"Output: {output_path}")

    # Initialize Modules
    try:
        loader = VideoLoader(input_path)
    except Exception as e:
        print(f"Error loading video: {e}")
        return

    estimator = PoseEstimator(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    normalizer = PoseNormalizer()
    smoother = TemporalSmoother(window_length=11, polyorder=3) # Offline smoothing better with window
    calculator = MotionCalculator()
    exporter = BVHExporter(output_path, fps=loader.fps)

    all_landmarks = []
    
    # 1. Extraction Pass
    print("Step 1: Extracting Pose...")
    frame_count = 0
    for frame in loader:
        results = estimator.process_frame(frame)
        landmarks = estimator.extract_world_landmarks(results)
        
        if landmarks is not None:
             all_landmarks.append(landmarks)
        else:
             # Handle missing data? 
             # For offline, we might want to interpolate later.
             # For now, append last known or NaN
             if all_landmarks:
                 all_landmarks.append(all_landmarks[-1])
             else:
                 all_landmarks.append(None) # Issues if start is empty

        frame_count += 1
        if frame_count % 100 == 0:
            print(f"  Processed {frame_count} frames...")
            
        if args.visualize:
            annotated = estimator.draw_landmarks(frame, results)
            cv2.imshow("Pose Extraction", annotated)
            if cv2.waitKey(1) & 0xFF == 27:
                break
                
    loader.release()
    cv2.destroyAllWindows()
    
    # Clean up empty starts if any
    all_landmarks = [l for l in all_landmarks if l is not None]
    
    if not all_landmarks:
        print("No pose detected in video.")
        return

    # 2. Smoothing Pass
    print("Step 2: Smoothing Data...")
    smoothed_landmarks = smoother.smooth_all(all_landmarks)
    
    # 3. Calculation & Export Pass
    print("Step 3: Calculating Motion & Exporting...")
    for i, landmarks in enumerate(smoothed_landmarks):
        # Normalize (Centering)
        norm_landmarks = normalizer.normalize_pose(landmarks)
        
        # Compute Angles
        rotations, root_pos = calculator.calculate_joint_angles(norm_landmarks)
        
        # Add to Exporter
        exporter.add_frame(root_pos, rotations)
        
    exporter.export()
    print("Done.")

if __name__ == "__main__":
    main()
