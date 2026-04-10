"""
app.py — AI Motion Animator  (Streamlit front-end)

Pipeline:  Video → MediaPipe pose estimation → BVH export → Three.js 3D viewer
"""

import base64
import os
import tempfile

import streamlit as st

from src.pipeline_runner import PipelineRunner
from src.viewer_utils import (
    generate_skeleton_viewer_html,
    generate_model_viewer_html,
    GLB_SIZE_LIMIT_MB,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Motion Animator",
    page_icon="🦴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Dark background override */
    .stApp { background: #0d0d14; color: #e0d8ff; }

    /* ── Header ── */
    .app-header {
        background: linear-gradient(135deg, #1a0a3c 0%, #0d0d14 60%, #0a1a3c 100%);
        border-bottom: 1px solid rgba(120,80,255,0.25);
        padding: 28px 32px 20px;
        margin-bottom: 4px;
    }
    .app-title {
        font-size: 2.1rem; font-weight: 700; letter-spacing: -0.5px;
        background: linear-gradient(90deg, #a080ff, #60a0ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .app-subtitle {
        color: #8070a0; font-size: 0.95rem; margin-top: 6px; font-weight: 400;
    }

    /* ── Section cards ── */
    .section-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(120,80,255,0.15);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #c0a8ff;
        margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #100d1e !important;
        border-right: 1px solid rgba(120,80,255,0.15);
    }
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 { color: #a080ff !important; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #5020c0, #2040a0);
        color: #fff; border: none; border-radius: 8px;
        padding: 10px 28px; font-size: 15px; font-weight: 500;
        transition: all 0.2s; box-shadow: 0 4px 14px rgba(80,32,180,0.4);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(80,32,180,0.6);
    }

    /* ── Progress bar ── */
    .stProgress > div > div { background: linear-gradient(90deg, #7850ff, #5080ff); border-radius: 4px; }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: rgba(80,180,80,0.15); border: 1px solid rgba(80,180,80,0.4);
        color: #80e080; border-radius: 8px;
    }
    .stDownloadButton > button:hover { background: rgba(80,180,80,0.3); }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.02);
        border: 1.5px dashed rgba(120,80,255,0.35);
        border-radius: 10px;
    }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(80,120,255,0.2);
        border-radius: 10px;
    }

    /* ── Info / warning ── */
    .stAlert { border-radius: 8px; }

    /* ── Slider track ── */
    [data-testid="stSlider"] > div > div > div > div { background: #7850ff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">🦴 AI Motion Animator</h1>
        <p class="app-subtitle">
            Upload a video of a person moving — the pipeline extracts their skeleton
            motion and renders it as an animated 3D rig. No external APIs required.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar — Processing Settings ────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Processing Settings")

    detection_conf = st.slider(
        "Detection Confidence",
        min_value=0.1, max_value=1.0, value=0.7, step=0.05,
        help="Minimum confidence for MediaPipe to detect a person in a frame.",
    )
    tracking_conf = st.slider(
        "Tracking Confidence",
        min_value=0.1, max_value=1.0, value=0.7, step=0.05,
        help="Minimum confidence to keep tracking across frames.",
    )
    smooth_window = st.slider(
        "Smoothing Window (frames)",
        min_value=3, max_value=31, value=11, step=2,
        help="Savitzky-Golay filter window. Larger = smoother but more lag.",
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#5a4a7a'>Skeleton is rendered via Three.js BVHLoader.<br>"
        "No internet connection is required for processing.</small>",
        unsafe_allow_html=True,
    )

# ── Main layout ───────────────────────────────────────────────────────────────
col_upload, col_settings = st.columns([3, 1], gap="large")

with col_upload:
    # ── Section 1: Upload Video ───────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📹 Step 1 — Upload Video</div>', unsafe_allow_html=True)

    uploaded_video = st.file_uploader(
        "Drag & drop or browse",
        type=["mp4", "mov", "avi", "mkv"],
        label_visibility="collapsed",
    )

    if uploaded_video:
        st.video(uploaded_video)
        st.caption(
            f"**{uploaded_video.name}** · "
            f"{uploaded_video.size / 1_048_576:.1f} MB"
        )
    else:
        st.info("Supported formats: MP4, MOV, AVI, MKV · Best results with a single clearly visible person.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 2: Process ────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚡ Step 2 — Extract Motion</div>', unsafe_allow_html=True)

    can_process = uploaded_video is not None
    process_btn = st.button(
        "🚀 Extract Motion & Generate 3D Skeleton",
        disabled=not can_process,
        use_container_width=True,
    )

    if not can_process:
        st.caption("Upload a video above to enable processing.")

    if can_process and process_btn:
        # Save video to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_video.read())
            video_path = tmp.name

        output_path = os.path.join("outputs", "animation.bvh")
        os.makedirs("outputs", exist_ok=True)

        status_placeholder = st.empty()
        progress_bar = st.progress(0, text="Initialising…")

        def on_progress(step: str, fraction: float):
            progress_bar.progress(min(fraction, 1.0), text=step)

        try:
            runner = PipelineRunner(
                min_detection_confidence=detection_conf,
                min_tracking_confidence=tracking_conf,
                smooth_window=smooth_window,
            )
            bvh_content = runner.run(
                video_path=video_path,
                output_path=output_path,
                progress_callback=on_progress,
            )
            st.session_state["bvh_content"] = bvh_content
            st.session_state["processed"] = True
            progress_bar.progress(1.0, text="✅ Done!")
            status_placeholder.success(
                f"Motion extracted successfully! "
                f"BVH saved to `{output_path}`."
            )
        except RuntimeError as e:
            progress_bar.empty()
            st.error(f"❌ {e}")
            st.session_state["processed"] = False
        finally:
            # On Windows, cv2.VideoCapture can briefly hold the file handle
            # even after .release() — silently skip deletion; OS cleans temp files.
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except PermissionError:
                pass

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 3: 3D Skeleton Viewer ────────────────────────────────
    if st.session_state.get("processed") and st.session_state.get("bvh_content"):
        bvh_content = st.session_state["bvh_content"]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">🦴 Step 3 — 3D Skeleton Preview</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Interact: **left-drag** to orbit · **right-drag** to pan · **scroll** to zoom. "
            "Use the controls below the viewer to play / scrub the animation."
        )

        viewer_html = generate_skeleton_viewer_html(bvh_content, width=860, height=540)
        st.html(viewer_html)

        st.download_button(
            label="⬇️ Download BVH Animation",
            data=bvh_content,
            file_name="motion_animation.bvh",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Section 4: Optional GLB Model Viewer ─────────────────────
        with st.expander(
            "🎭 Load 3D Model (optional) — apply animation to your own GLB character",
            expanded=False,
        ):
            st.markdown(
                "Upload a rigged humanoid GLB (e.g. from [Mixamo](https://www.mixamo.com/) "
                "or [Sketchfab](https://sketchfab.com/)) and the skeleton animation will be "
                "retargeted onto it. Bone names must follow **Mixamo** naming convention for "
                "best results."
            )

            glb_tab_upload, glb_tab_url = st.tabs(["📁 Upload GLB file", "🔗 Use GLB URL"])

            selected_glb_b64 = None
            model_source_label = ""

            with glb_tab_upload:
                glb_file = st.file_uploader(
                    f"Upload GLB file (max {GLB_SIZE_LIMIT_MB} MB)",
                    type=["glb"],
                    key="glb_uploader",
                )
                if glb_file:
                    size_mb = glb_file.size / 1_048_576
                    if size_mb > GLB_SIZE_LIMIT_MB:
                        st.error(
                            f"⚠️ File is {size_mb:.1f} MB — the limit is {GLB_SIZE_LIMIT_MB} MB. "
                            "Please use a smaller model to avoid freezing the browser tab."
                        )
                    else:
                        selected_glb_b64 = base64.b64encode(glb_file.read()).decode("utf-8")
                        model_source_label = glb_file.name
                        st.success(f"✅ Loaded **{glb_file.name}** ({size_mb:.1f} MB)")

            with glb_tab_url:
                glb_url = st.text_input(
                    "Public GLB URL",
                    placeholder="https://models.readyplayer.me/xxxx.glb",
                    key="glb_url",
                )
                if glb_url:
                    st.info(
                        "URL-based models are loaded directly by the browser (CORS must allow it). "
                        "If the model fails to appear, try uploading the file instead."
                    )
                    # We pass the URL directly; the viewer will fetch it with GLTFLoader
                    selected_glb_b64 = None  # signal to use URL path below
                    model_source_label = glb_url

            if selected_glb_b64 is not None:
                # Uploaded file path: embed as base64
                model_viewer_html = generate_model_viewer_html(
                    glb_b64=selected_glb_b64,
                    bvh_content=bvh_content,
                    width=860,
                    height=540,
                )
                st.html(model_viewer_html)

            elif glb_url:
                _url_viewer = _build_url_model_viewer(glb_url, bvh_content, width=860, height=540)
                st.html(_url_viewer)


with col_settings:
    st.markdown(
        """
        <div class="section-card" style="position:sticky;top:80px;">
        <div class="section-title">💡 Tips</div>
        <ul style="color:#9080b0;font-size:0.88rem;line-height:1.7;padding-left:16px;">
            <li>Use well-lit, single-person video</li>
            <li>Full-body visible in most frames</li>
            <li>MP4 / H.264 recommended</li>
            <li>Short clips (10–60 s) process fastest</li>
            <li>Lower confidence → more detections, more noise</li>
            <li>Higher smoothing → smoother motion, more lag</li>
        </ul>
        <hr style="border-color:rgba(120,80,255,0.15);margin:14px 0">
        <div style="color:#5a4a7a;font-size:0.8rem;">
            <b style="color:#7a6a9a">Output format</b><br>
            BVH (BioVision Hierarchy) — compatible with Blender, Maya, MotionBuilder, Unity, and Unreal Engine.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── URL-based model viewer (separate helper — no external import needed) ──────
def _build_url_model_viewer(glb_url: str, bvh_content: str, width: int, height: int) -> str:
    """Viewer that loads a GLB by URL (browser fetches it, CORS-permitting)."""
    from src.viewer_utils import _THREE, _ORBIT, _GLTF, _BVH
    bvh_b64 = base64.b64encode(bvh_content.encode("utf-8")).decode("utf-8")

    return (
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Model Viewer</title>'
        f'<style>*{{margin:0;padding:0;box-sizing:border-box;}}'
        f'body{{background:#0d0d14;overflow:hidden;font-family:\'Segoe UI\',sans-serif;}}'
        f'#cv{{width:{width}px;height:{height}px;position:relative;}}'
        f'#ov{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;background:#0d0d14;color:#8090c0;font-size:14px;gap:12px;pointer-events:none;}}'
        f'.sp{{width:36px;height:36px;border:3px solid rgba(80,120,255,.2);'
        f'border-top-color:#5080ff;border-radius:50%;animation:spin .8s linear infinite;}}'
        f'@keyframes spin{{to{{transform:rotate(360deg)}}}}</style></head><body>'
        f'<div id="cv"><div id="ov"><div class="sp"></div><span>Loading model…</span></div></div>'
        f'<script type="module">'
        f'import * as THREE from "{_THREE}";'
        f'import {{OrbitControls}} from "{_ORBIT}";'
        f'import {{GLTFLoader}} from "{_GLTF}";'
        f'import {{BVHLoader}} from "{_BVH}";'
        f'const W={width},H={height};'
        f'const renderer=new THREE.WebGLRenderer({{antialias:true}});'
        f'renderer.setSize(W,H);renderer.shadowMap.enabled=true;'
        f'document.getElementById("cv").prepend(renderer.domElement);'
        f'const scene=new THREE.Scene();scene.background=new THREE.Color(0x0d0d14);'
        f'scene.add(new THREE.AmbientLight(0xffffff,.8));'
        f'const dl=new THREE.DirectionalLight(0xffffff,2.5);dl.position.set(4,10,6);scene.add(dl);'
        f'const camera=new THREE.PerspectiveCamera(45,W/H,.01,200);'
        f'camera.position.set(0,1.5,4);'
        f'const ctl=new OrbitControls(camera,renderer.domElement);'
        f'ctl.target.set(0,1,0);ctl.enableDamping=true;ctl.update();'
        f'const bvh=new BVHLoader().parse(atob("{bvh_b64}"));'
        f'const clip=bvh.clip;let mixer;'
        f'new GLTFLoader().load("{glb_url}",gltf=>{{scene.add(gltf.scene);'
        f'mixer=new THREE.AnimationMixer(gltf.scene);'
        f'const bm={{}};gltf.scene.traverse(o=>{{bm[o.name]=o;}});'
        f'const tracks=clip.tracks.filter(t=>{{const m=t.name.match(/\\[(.+?)\\]/);return m&&!!bm[m[1]];}});'
        f'mixer.clipAction(new THREE.AnimationClip(clip.name,clip.duration,tracks)).play();'
        f'document.getElementById("ov").style.display="none";}}'
        f',undefined,()=>{{document.getElementById("ov").innerHTML'
        f'=\'<span style="color:#ff6060">CORS error or invalid URL</span>\';}});'
        f'const clock=new THREE.Clock();'
        f'(function animate(){{requestAnimationFrame(animate);'
        f'if(mixer)mixer.update(clock.getDelta());'
        f'ctl.update();renderer.render(scene,camera);}})();'
        f'</script></body></html>'
    )

