import mediapipe as mp
import cv2
import numpy as np
from .config import MP_NOSE, MP_LEFT_FOOT_INDEX

class PoseEstimator:
    def __init__(self, static_image_mode=False, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initialize MediaPipe Pose Estimator.
        
        Args:
            static_image_mode (bool): Whether to treat input images as a batch of static and possibly unrelated images.
            model_complexity (int): Complexity of the pose landmark model: 0, 1 or 2.
            min_detection_confidence (float): Minimum confidence value ([0.0, 1.0]) for the detection to be considered successful.
            min_tracking_confidence (float): Minimum confidence value ([0.0, 1.0]) for the landmark-tracking model phase.
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def process_frame(self, frame):
        """
        Process a single frame and extract landmarks.
        
        Args:
            frame (np.array): BGR image frame.
            
        Returns:
            results: MediaPipe pose results object.
            landmarks_world: World landmarks (3D) if detected, else None.
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process
        results = self.pose.process(image_rgb)
        
        return results

    def extract_landmarks(self, results):
        """
        Extract landmarks as a numpy array.
        
        Args:
            results: MediaPipe pose results object.
            
        Returns:
            landmarks (np.array): Shape (33, 4) -> [x, y, z, visibility]. Returns None if no landmarks detected.
        """
        if not results.pose_landmarks:
            return None
            
        # 33 landmarks, 4 values (x, y, z, visibility)
        landmarks = np.zeros((33, 4))
        
        for i, landmark in enumerate(results.pose_landmarks.landmark):
            landmarks[i] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
            
        return landmarks
        
    def extract_world_landmarks(self, results):
        """
        Extract world landmarks (meters) as a numpy array.
        MediaPipe World landmarks are in meters with origin at the center of the hips.
        
        Args:
            results: MediaPipe pose results object.
        
        Returns:
             landmarks (np.array): Shape (33, 4) -> [x, y, z, visibility]. Returns None if no landmarks detected.
        """
        if not results.pose_world_landmarks:
            return None
            
        landmarks = np.zeros((33, 4))
        
        for i, landmark in enumerate(results.pose_world_landmarks.landmark):
            landmarks[i] = [landmark.x, landmark.y, landmark.z, landmark.visibility]
            
        return landmarks

    def draw_landmarks(self, frame, results):
        """Draw landmarks on the frame."""
        annotated_image = frame.copy()
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
        return annotated_image
