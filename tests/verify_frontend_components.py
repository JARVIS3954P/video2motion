import sys
import os

# Add project root to path
# Assumes script is in tests/ directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.avatar_handler import AvatarHandler
    from src.viewer_utils import generate_viewer_html
    from src.motion_calculator import MotionCalculator
    from src.config import SKELETON_HIERARCHY
    print("Imports successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_avatar_handler():
    handler = AvatarHandler()
    url = handler.get_avatar_url()
    print(f"Avatar URL: {url}")
    assert url.startswith("http"), "Avatar URL should start with http"
    # assert url.endswith(".glb"), "Avatar URL should end with .glb" # Not strictly required if URL params exist

def test_viewer_utils():
    html = generate_viewer_html("http://example.com/avatar.glb", "HIERARCHY...")
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
    test_avatar_handler()
    test_viewer_utils()
    test_motion_calculator_init()
    print("Verification complete.")
