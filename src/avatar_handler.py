import os
import requests

class AvatarHandler:
    def __init__(self):
        # Default avatar URL (a standard masculine/feminine or neutral model from Ready Player Me)
        # Using a public demo model
        self.default_avatar_url = "https://models.readyplayer.me/64b54e3d3604f32997d51922.glb" 
        self.avatar_dir = "outputs/avatars"
        os.makedirs(self.avatar_dir, exist_ok=True)

    def get_avatar_url(self, photo_path=None):
        """
        Returns the URL or local path to the avatar GLB.
        If photo_path is provided, attempts to generate an avatar (Placeholder).
        Otherwise returns default.
        """
        if photo_path:
            # TODO: Implement Ready Player Me API for photo-to-avatar
            # Requires API Key and network request.
            # For now, we simulate by returning the default, but we could validly 
            # Implement if the user provides an API key in env vars.
            print(f"Generating avatar from {photo_path} (Simulation)...")
            return self.default_avatar_url
        
        return self.default_avatar_url

    def download_avatar(self, url, filename):
        """Downloads the avatar to local storage."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            path = os.path.join(self.avatar_dir, filename)
            with open(path, 'wb') as f:
                f.write(response.content)
            return path
        except Exception as e:
            print(f"Failed to download avatar: {e}")
            return None
