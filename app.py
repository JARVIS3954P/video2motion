import streamlit as st
import os
import tempfile
import time
from src.avatar_handler import AvatarHandler
from src.viewer_utils import generate_viewer_html
import streamlit.components.v1 as components
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
    avatar_url = avatar_handler.get_avatar_url("dummy_path") 
else:
    avatar_url = avatar_handler.get_avatar_url()

st.sidebar.image(avatar_url.replace(".glb", ".png") if "readyplayer.me" in avatar_url else "resources/icon_avatar.jpg", 
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
            # --- Simulated Pipeline Start ---
            status_text.text("Initializing Pipeline...")
            time.sleep(1)
            
            # 1. Extraction
            status_text.text("Step 1/3: Extracting Pose Data (This may take a moment)...")
            for i in range(100):
                time.sleep(0.03)  # simulates processing 100 frames
                if i % 10 == 0:
                     progress_bar.progress(min(i / 100, 1.0) * 0.5)

            # 2. Smoothing
            status_text.text("Step 2/3: Smoothing Motion...")
            time.sleep(1.5)
            progress_bar.progress(0.6)
            
            # 3. Calculation & Export
            status_text.text("Step 3/3: Calculating Joint Angles & Exporting...")
            
            for i in range(100):
                time.sleep(0.02)
                if i % 10 == 0:
                    progress_bar.progress(0.6 + (i / 100) * 0.4)
                    
            progress_bar.progress(1.0)
            status_text.text("Done!")
            
            # --- Simulated Pipeline End ---
            
            # Read Fake BVH Content
            fake_bvh_path = os.path.join("outputs", "mock_test.bvh")
            if os.path.exists(fake_bvh_path):
                with open(fake_bvh_path, 'r') as f:
                    bvh_content = f.read()
            else:
                bvh_content = "HIERARCHY\nROOT Hips\n{\n  OFFSET 0.00 0.00 0.00\n  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n  End Site\n  {\n    OFFSET 0.00 10.00 0.00\n  }\n}\nMOTION\nFrames: 1\nFrame Time: 0.0333333\n0.0 0.0 0.0 0.0 0.0 0.0"
            
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
