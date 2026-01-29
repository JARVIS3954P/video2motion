import numpy as np

# MediaPipe Pose Landmark Indices
# https://developers.google.com/mediapipe/solutions/vision/pose
MP_NOSE = 0
MP_LEFT_SHOULDER = 11
MP_RIGHT_SHOULDER = 12
MP_LEFT_ELBOW = 13
MP_RIGHT_ELBOW = 14
MP_LEFT_WRIST = 15
MP_RIGHT_WRIST = 16
MP_LEFT_HIP = 23
MP_RIGHT_HIP = 24
MP_LEFT_KNEE = 25
MP_RIGHT_KNEE = 26
MP_LEFT_ANKLE = 27
MP_RIGHT_ANKLE = 28
MP_LEFT_HEEL = 29
MP_RIGHT_HEEL = 30
MP_LEFT_FOOT_INDEX = 31
MP_RIGHT_FOOT_INDEX = 32

# BVH Skeleton Definition
# Hierarchical structure: Parent -> Children
SKELETON_HIERARCHY = {
    'Hips': ['Spine', 'RightUpLeg', 'LeftUpLeg'],
    'Spine': ['Spine1'],
    'Spine1': ['Neck', 'RightShoulder', 'LeftShoulder'],
    'Neck': ['Head'],
    'Head': [],
    'RightShoulder': ['RightArm'],
    'RightArm': ['RightForeArm'],
    'RightForeArm': ['RightHand'],
    'RightHand': [],
    'LeftShoulder': ['LeftArm'],
    'LeftArm': ['LeftForeArm'],
    'LeftForeArm': ['LeftHand'],
    'LeftHand': [],
    'RightUpLeg': ['RightLeg'],
    'RightLeg': ['RightFoot'],
    'RightFoot': [],
    'LeftUpLeg': ['LeftLeg'],
    'LeftLeg': ['LeftFoot'],
    'LeftFoot': []
}

# Mapping: BVH Joint Name -> List of MediaPipe Landmarks to derive position from
# For simple joints, it's a 1-to-1 mapping. For Hips, it's often the midpoint of Left and Right Hips.
LANDMARK_MAP = {
    'Hips': [MP_LEFT_HIP, MP_RIGHT_HIP], # Midpoint
    'Spine': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP], # Approximate center of torso
    'Spine1': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER], # Midpoint of shoulders
    'Neck': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER], # Often same as spine top, close to shoulders
    'Head': [MP_NOSE], # Nose or midpoint of ears
    'RightShoulder': [MP_RIGHT_SHOULDER],
    'RightArm': [MP_RIGHT_SHOULDER], # Upper arm starts at shoulder
    'RightForeArm': [MP_RIGHT_ELBOW],
    'RightHand': [MP_RIGHT_WRIST],
    'LeftShoulder': [MP_LEFT_SHOULDER],
    'LeftArm': [MP_LEFT_SHOULDER],
    'LeftForeArm': [MP_LEFT_ELBOW],
    'LeftHand': [MP_LEFT_WRIST],
    'RightUpLeg': [MP_RIGHT_HIP],
    'RightLeg': [MP_RIGHT_KNEE],
    'RightFoot': [MP_RIGHT_ANKLE],
    'LeftUpLeg': [MP_LEFT_HIP],
    'LeftLeg': [MP_LEFT_KNEE],
    'LeftFoot': [MP_LEFT_ANKLE]
}

# Rest Pose Offsets (T-Pose usually)
# These are relative offsets from parent to child in the Zero-Rotation pose.
# Start with a standard unit scale, can be calibrated later.
# Units: Arbitrary (e.g., cm or meters), usually consistent with BVH standards (often inches or cm).
# This is a template; might need adjustment based on specific rig.
REST_POSE_OFFSETS = {
    'Hips': np.array([0.0, 0.0, 0.0]), # Root, global position
    'Spine': np.array([0.0, 10.0, 0.0]),
    'Spine1': np.array([0.0, 10.0, 0.0]),
    'Neck': np.array([0.0, 5.0, 0.0]),
    'Head': np.array([0.0, 5.0, 0.0]),
    'RightShoulder': np.array([-5.0, 10.0, 0.0]), # Relative to Spine1
    'RightArm': np.array([-5.0, 0.0, 0.0]),
    'RightForeArm': np.array([-10.0, 0.0, 0.0]),
    'RightHand': np.array([-10.0, 0.0, 0.0]),
    'LeftShoulder': np.array([5.0, 10.0, 0.0]),
    'LeftArm': np.array([5.0, 0.0, 0.0]),
    'LeftForeArm': np.array([10.0, 0.0, 0.0]),
    'LeftHand': np.array([10.0, 0.0, 0.0]),
    'RightUpLeg': np.array([-5.0, -5.0, 0.0]), # Relative to Hips
    'RightLeg': np.array([0.0, -15.0, 0.0]),
    'RightFoot': np.array([0.0, -15.0, 0.0]),
    'LeftUpLeg': np.array([5.0, -5.0, 0.0]),
    'LeftLeg': np.array([0.0, -15.0, 0.0]),
    'LeftFoot': np.array([0.0, -15.0, 0.0])
}
