import streamlit as st
import os
import tempfile
import cv2
import time
from src.video_loader import VideoLoader
from src.pose_estimator import PoseEstimator
from src.pose_processing import PoseNormalizer, TemporalSmoother
from src.motion_calculator import MotionCalculator
from src.bvh_exporter import BVHExporter
from src.avatar_handler import AvatarHandler
from src.viewer_utils import generate_viewer_html
import streamlit.components.v1 as components

# Page Config
st.set_page_config(page_title="AI Motion Animator", layout="wide")

st.title("AI Motion Animator")
st.markdown("Transform your videos into 3D animations with a custom avatar.")

# Sidebar - Avatar Settings
st.sidebar.header("1. Your Avatar")
avatar_handler = AvatarHandler()

uploaded_photo = st.sidebar.file_uploader("Upload Selfie (Optional)", type=['jpg', 'png', 'jpeg'])
if uploaded_photo:
    st.sidebar.info("Generative Avatar feature coming soon! Using standard avatar.")
    # In a real app, save photo and pass path to handler
    # photo_path = save_temp(uploaded_photo)
    # avatar_url = avatar_handler.get_avatar_url(photo_path)
    avatar_url = avatar_handler.get_avatar_url("dummy_path") 
else:
    avatar_url = avatar_handler.get_avatar_url()

st.sidebar.image(avatar_url.replace(".glb", ".png") if "readyplayer.me" in avatar_url else "https://via.placeholder.com/150", 
                 caption="Active Avatar", width=150)
st.sidebar.markdown(f"[Download Avatar]({avatar_url})")


# Main Area - Video Processing
st.header("2. Motion Extraction")

uploaded_video = st.file_uploader("Upload a Video (MP4, MOV, AVI)", type=['mp4', 'mov', 'avi'])

if uploaded_video:
    # Save video to temp file
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_video.read())
    tfile.close()
    video_path = tfile.name

    st.video(video_path)

    if st.button("Extract Motion & Animate"):
        output_path = os.path.join("outputs", "temp_animation.bvh")
        os.makedirs("outputs", exist_ok=True)
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # --- Pipeline Start ---
            status_text.text("Initializing Pipeline...")
            
            try:
                loader = VideoLoader(video_path)
            except Exception as e:
                st.error(f"Error loading video: {e}")
                st.stop()

            estimator = PoseEstimator(min_detection_confidence=0.7, min_tracking_confidence=0.7)
            normalizer = PoseNormalizer()
            smoother = TemporalSmoother(window_length=11, polyorder=3)
            calculator = MotionCalculator()
            exporter = BVHExporter(output_path, fps=loader.fps)
            
            all_landmarks = []
            
            # 1. Extraction
            status_text.text("Step 1/3: Extracting Pose Data (This may take a moment)...")
            
            total_frames = int(loader.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if loader.cap.isOpened() else 100
            frame_count = 0
            
            for frame in loader:
                results = estimator.process_frame(frame)
                landmarks = estimator.extract_world_landmarks(results)
                
                if landmarks is not None:
                    all_landmarks.append(landmarks)
                else:
                    # Handle missing data (use last valid or empty)
                    if all_landmarks:
                        all_landmarks.append(all_landmarks[-1])
                    else:
                        all_landmarks.append(None)
                        
                frame_count += 1
                if frame_count % 10 == 0:
                     progress_bar.progress(min(frame_count / total_frames, 1.0) * 0.5)

            loader.release()
            
            # Clean up empty starts
            all_landmarks = [l for l in all_landmarks if l is not None]
            
            if not all_landmarks:
                st.error("No pose detected in video.")
                st.stop()

            # 2. Smoothing
            status_text.text("Step 2/3: Smoothing Motion...")
            smoothed_landmarks = smoother.smooth_all(all_landmarks)
            progress_bar.progress(0.6)
            
            # 3. Calculation & Export
            status_text.text("Step 3/3: Calculating Joint Angles & Exporting...")
            
            for i, landmarks in enumerate(smoothed_landmarks):
                # Normalize
                norm_landmarks = normalizer.normalize_pose(landmarks)
                # Calculate
                rotations, root_pos = calculator.calculate_joint_angles(norm_landmarks)
                # Add Frame
                exporter.add_frame(root_pos, rotations)
                
                if i % 10 == 0:
                    progress_bar.progress(0.6 + (i / len(smoothed_landmarks)) * 0.4)
                    
            exporter.export()
            progress_bar.progress(1.0)
            status_text.text("Done!")
            
            # --- Pipeline End ---
            
            # Read BVH Content
            with open(output_path, 'r') as f:
                bvh_content = f.read()
            
            # Generate Viewer
            st.header("3. 3D Preview")
            viewer_html = generate_viewer_html(avatar_url, bvh_content, width=800, height=500)
            components.html(viewer_html, height=500)
            
            # Download Button
            st.download_button("Download BVH Animation", bvh_content, file_name="animation.bvh")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            # Clean up temp file
            if os.path.exists(video_path):
                os.remove(video_path)
            raise e
