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
# BVH Skeleton Definition
# Hierarchical structure: Parent -> Children
# Matches Mixamo/ReadyPlayerMe Rig
SKELETON_HIERARCHY = {
    'Hips': ['Spine', 'RightUpLeg', 'LeftUpLeg'],
    'Spine': ['Spine1'],
    'Spine1': ['Spine2'],
    'Spine2': ['Neck', 'RightShoulder', 'LeftShoulder'],
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
LANDMARK_MAP = {
    'Hips': [MP_LEFT_HIP, MP_RIGHT_HIP], # Midpoint
    'Spine': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP], # Lower/Mid Spine approximation
    'Spine1': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP], # Mid/Upper Spine approximation
    'Spine2': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER], # Upper Chest
    'Neck': [MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER], # Neck base
    'Head': [MP_NOSE], 
    'RightShoulder': [MP_RIGHT_SHOULDER],
    'RightArm': [MP_RIGHT_SHOULDER], 
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
# Adjusted for a standard humanoid rig (Mixamo/RPM style)
# Units: cm (approximate)
REST_POSE_OFFSETS = {
    'Hips': np.array([0.0, 100.0, 0.0]), # Root height ~1m
    'Spine': np.array([0.0, 10.0, 0.0]),
    'Spine1': np.array([0.0, 10.0, 0.0]),
    'Spine2': np.array([0.0, 10.0, 0.0]),
    'Neck': np.array([0.0, 10.0, 0.0]),
    'Head': np.array([0.0, 10.0, 0.0]),
    'RightShoulder': np.array([-5.0, 10.0, 0.0]), # Clavicle
    'RightArm': np.array([-10.0, 0.0, 0.0]),
    'RightForeArm': np.array([-25.0, 0.0, 0.0]),
    'RightHand': np.array([-25.0, 0.0, 0.0]),
    'LeftShoulder': np.array([5.0, 10.0, 0.0]), # Clavicle
    'LeftArm': np.array([10.0, 0.0, 0.0]),
    'LeftForeArm': np.array([25.0, 0.0, 0.0]),
    'LeftHand': np.array([25.0, 0.0, 0.0]),
    'RightUpLeg': np.array([-10.0, -5.0, 0.0]), 
    'RightLeg': np.array([0.0, -40.0, 0.0]),
    'RightFoot': np.array([0.0, -40.0, 0.0]),
    'LeftUpLeg': np.array([10.0, -5.0, 0.0]),
    'LeftLeg': np.array([0.0, -40.0, 0.0]),
    'LeftFoot': np.array([0.0, -40.0, 0.0])
}
