import numpy as np
from scipy.signal import savgol_filter
from .config import MP_LEFT_HIP, MP_RIGHT_HIP

class PoseNormalizer:
    def __init__(self):
        pass

    def normalize_pose(self, landmarks):
        """
        Normalize pose landmarks to be subject-centric.
        1. Translate so midpoint of hips is at (0,0,0).
        2. (Optional) Scale normalization can be added here if needed, but 
           usually for BVH, we keep the relative scale or normalize to a standard height.
           Here we will return the hip-centered coordinates.
        
        Args:
            landmarks (np.array): Shape (33, 4) [x, y, z, visibility]
            
        Returns:
            normalized_landmarks (np.array): Shape (33, 4)
        """
        if landmarks is None:
            return None
            
        # visual copy
        norm_landmarks = landmarks.copy()
        
        # Calculate Hip Center (Root)
        # We need to handle visibility? For now, assume hips are visible if we are tracking.
        left_hip = landmarks[MP_LEFT_HIP, :3]
        right_hip = landmarks[MP_RIGHT_HIP, :3]
        hip_center = (left_hip + right_hip) / 2.0
        
        # Translate all joints
        norm_landmarks[:, :3] -= hip_center
        
        return norm_landmarks

class TemporalSmoother:
    def __init__(self, window_length=5, polyorder=2):
        """
        Initialize temporal smoother using Savitzky-Golay filter.
        
        Args:
            window_length (int): Length of the filter window (must be odd).
            polyorder (int): Order of the polynomial to fit.
        """
        self.window_length = window_length
        self.polyorder = polyorder
        self.pose_buffer = []

    def update(self, landmarks):
        """
        Add new landmarks to buffer and return smoothed version.
        Note: Real-time smoothing introduces lag.
        For offline processing, we should collect ALL frames and smooth at once.
        This method is for a buffer-based approach.
        
        Args:
            landmarks (np.array): Shape (33, 4)
            
        Returns:
            smoothed_landmarks (np.array): Shape (33, 4) or None if buffer not full enough for first frame? 
            Actually for basic smoothing we might just return the latest smoothed point or 
            if we are offline, we shouldn't use this per-frame update for the final result.
        """
        self.pose_buffer.append(landmarks)
        # Keep buffer manageable? No, for offline we want the whole sequence.
        # But this class might be used per-frame.
        # Let's define a separate method for batch smoothing.
        return landmarks # Pass-through if used per-frame without delay logic

    def smooth_all(self, all_landmarks):
        """
        Smooth the entire sequence of landmarks.
        
        Args:
            all_landmarks (list of np.array): List of (33, 4) arrays.
            
        Returns:
            smoothed_sequence (np.array): Shape (F, 33, 4)
        """
        data = np.array(all_landmarks) # Shape (Frames, 33, 4)
        F, J, C = data.shape
        
        smoothed_data = np.empty_like(data)
        
        # Filter each coordinate of each joint independently
        # We don't smooth visibility (index 3)
        smoothed_data[:, :, 3] = data[:, :, 3]
        
        # Check if we have enough frames
        if F <= self.window_length:
            print("Warning: Not enough frames for smoothing, returning original data.")
            return data

        for j in range(J):
            for c in range(3): # x, y, z
                smoothed_data[:, j, c] = savgol_filter(data[:, j, c], self.window_length, self.polyorder)
                
        return smoothed_data
