import sys
import os

# Add project root to path
# Assumes script is in tests/ directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.video_motion.utils.viewer_utils import generate_skeleton_viewer_html
    from src.video_motion.core.motion_calculator import MotionCalculator
    from src.video_motion.config import SKELETON_HIERARCHY
    print("Imports successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_viewer_utils():
    # AvatarHandler was removed, skipping test
    html = generate_skeleton_viewer_html("HIERARCHY...", width=800, height=600)
    assert "<!DOCTYPE html>" in html
    assert "three.module.js" in html
    assert "BVHLoader.js" in html
    print("Viewer HTML generation successful.")

def test_motion_calculator_init():
    try:
        mc = MotionCalculator()
        print("MotionCalculator initialized successfully.")
    except Exception as e:
        print(f"MotionCalculator init failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_viewer_utils()
    test_motion_calculator_init()
    print("Verification complete.")
