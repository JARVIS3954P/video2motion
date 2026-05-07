from dataclasses import dataclass

import numpy as np


# MediaPipe Pose Landmark Indices
# https://developers.google.com/mediapipe/solutions/vision/pose
MP_NOSE = 0
MP_LEFT_EYE_INNER = 1
MP_LEFT_EYE = 2
MP_LEFT_EYE_OUTER = 3
MP_RIGHT_EYE_INNER = 4
MP_RIGHT_EYE = 5
MP_RIGHT_EYE_OUTER = 6
MP_LEFT_EAR = 7
MP_RIGHT_EAR = 8
MP_MOUTH_LEFT = 9
MP_MOUTH_RIGHT = 10
MP_LEFT_SHOULDER = 11
MP_RIGHT_SHOULDER = 12
MP_LEFT_ELBOW = 13
MP_RIGHT_ELBOW = 14
MP_LEFT_WRIST = 15
MP_RIGHT_WRIST = 16
MP_LEFT_PINKY = 17
MP_RIGHT_PINKY = 18
MP_LEFT_INDEX = 19
MP_RIGHT_INDEX = 20
MP_LEFT_THUMB = 21
MP_RIGHT_THUMB = 22
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


@dataclass(frozen=True)
class JointSpec:
    name: str
    parent: str | None
    offset: tuple[float, float, float]
    landmarks: tuple[int, ...] = ()
    aliases: tuple[str, ...] = ()


JOINT_SPECS = (
    JointSpec("Hips", None, (0.0, 0.0, 0.0), (MP_LEFT_HIP, MP_RIGHT_HIP), ("mixamorig:Hips",)),
    JointSpec("Spine", "Hips", (0.0, 0.1, 0.0), (MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP), ("mixamorig:Spine",)),
    JointSpec("Spine1", "Spine", (0.0, 0.1, 0.0), (MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP), ("mixamorig:Spine1",)),
    JointSpec("Spine2", "Spine1", (0.0, 0.1, 0.0), (MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER, MP_LEFT_HIP, MP_RIGHT_HIP), ("mixamorig:Spine2",)),
    JointSpec("Neck", "Spine2", (0.0, 0.1, 0.0), (MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER), ("mixamorig:Neck",)),
    JointSpec("Head", "Neck", (0.0, 0.1, 0.0), (MP_LEFT_EAR, MP_RIGHT_EAR), ("mixamorig:Head",)),
    JointSpec("HeadEnd", "Head", (0.0, 0.1, 0.1), (MP_NOSE,)),
    JointSpec("RightShoulder", "Spine2", (-0.05, 0.1, 0.0), (MP_RIGHT_SHOULDER,), ("mixamorig:RightShoulder",)),
    JointSpec("RightArm", "RightShoulder", (-0.1, 0.0, 0.0), (MP_RIGHT_SHOULDER,), ("mixamorig:RightArm",)),
    JointSpec("RightForeArm", "RightArm", (-0.25, 0.0, 0.0), (MP_RIGHT_ELBOW,), ("mixamorig:RightForeArm",)),
    JointSpec("RightHand", "RightForeArm", (-0.25, 0.0, 0.0), (MP_RIGHT_WRIST,), ("mixamorig:RightHand",)),
    JointSpec("RightIndex1", "RightHand", (-0.025, 0.0, 0.035), (MP_RIGHT_INDEX,), ("mixamorig:RightHandIndex1",)),
    JointSpec("RightIndexEnd", "RightIndex1", (-0.035, 0.0, 0.02), (MP_RIGHT_INDEX,)),
    JointSpec("RightPinky1", "RightHand", (-0.025, 0.0, -0.03), (MP_RIGHT_PINKY,), ("mixamorig:RightHandPinky1",)),
    JointSpec("RightPinkyEnd", "RightPinky1", (-0.03, 0.0, -0.018), (MP_RIGHT_PINKY,)),
    JointSpec("RightThumb1", "RightHand", (-0.02, -0.015, 0.045), (MP_RIGHT_THUMB,), ("mixamorig:RightHandThumb1",)),
    JointSpec("RightThumbEnd", "RightThumb1", (-0.03, -0.01, 0.025), (MP_RIGHT_THUMB,)),
    JointSpec("LeftShoulder", "Spine2", (0.05, 0.1, 0.0), (MP_LEFT_SHOULDER,), ("mixamorig:LeftShoulder",)),
    JointSpec("LeftArm", "LeftShoulder", (0.1, 0.0, 0.0), (MP_LEFT_SHOULDER,), ("mixamorig:LeftArm",)),
    JointSpec("LeftForeArm", "LeftArm", (0.25, 0.0, 0.0), (MP_LEFT_ELBOW,), ("mixamorig:LeftForeArm",)),
    JointSpec("LeftHand", "LeftForeArm", (0.25, 0.0, 0.0), (MP_LEFT_WRIST,), ("mixamorig:LeftHand",)),
    JointSpec("LeftIndex1", "LeftHand", (0.025, 0.0, 0.035), (MP_LEFT_INDEX,), ("mixamorig:LeftHandIndex1",)),
    JointSpec("LeftIndexEnd", "LeftIndex1", (0.035, 0.0, 0.02), (MP_LEFT_INDEX,)),
    JointSpec("LeftPinky1", "LeftHand", (0.025, 0.0, -0.03), (MP_LEFT_PINKY,), ("mixamorig:LeftHandPinky1",)),
    JointSpec("LeftPinkyEnd", "LeftPinky1", (0.03, 0.0, -0.018), (MP_LEFT_PINKY,)),
    JointSpec("LeftThumb1", "LeftHand", (0.02, -0.015, 0.045), (MP_LEFT_THUMB,), ("mixamorig:LeftHandThumb1",)),
    JointSpec("LeftThumbEnd", "LeftThumb1", (0.03, -0.01, 0.025), (MP_LEFT_THUMB,)),
    JointSpec("RightUpLeg", "Hips", (-0.1, -0.05, 0.0), (MP_RIGHT_HIP,), ("mixamorig:RightUpLeg",)),
    JointSpec("RightLeg", "RightUpLeg", (0.0, -0.4, 0.0), (MP_RIGHT_KNEE,), ("mixamorig:RightLeg",)),
    JointSpec("RightFoot", "RightLeg", (0.0, -0.4, 0.0), (MP_RIGHT_ANKLE,), ("mixamorig:RightFoot",)),
    JointSpec("RightToeBase", "RightFoot", (0.0, -0.05, 0.1), (MP_RIGHT_HEEL, MP_RIGHT_FOOT_INDEX), ("mixamorig:RightToeBase",)),
    JointSpec("RightToeEnd", "RightToeBase", (0.0, 0.0, 0.1), (MP_RIGHT_FOOT_INDEX,)),
    JointSpec("LeftUpLeg", "Hips", (0.1, -0.05, 0.0), (MP_LEFT_HIP,), ("mixamorig:LeftUpLeg",)),
    JointSpec("LeftLeg", "LeftUpLeg", (0.0, -0.4, 0.0), (MP_LEFT_KNEE,), ("mixamorig:LeftLeg",)),
    JointSpec("LeftFoot", "LeftLeg", (0.0, -0.4, 0.0), (MP_LEFT_ANKLE,), ("mixamorig:LeftFoot",)),
    JointSpec("LeftToeBase", "LeftFoot", (0.0, -0.05, 0.1), (MP_LEFT_HEEL, MP_LEFT_FOOT_INDEX), ("mixamorig:LeftToeBase",)),
    JointSpec("LeftToeEnd", "LeftToeBase", (0.0, 0.0, 0.1), (MP_LEFT_FOOT_INDEX,)),
)

JOINT_NAMES = tuple(spec.name for spec in JOINT_SPECS)
JOINT_PARENT = {spec.name: spec.parent for spec in JOINT_SPECS}
JOINT_ALIASES = {spec.name: spec.aliases for spec in JOINT_SPECS}

SKELETON_HIERARCHY = {spec.name: [] for spec in JOINT_SPECS}
for spec in JOINT_SPECS:
    if spec.parent is not None:
        SKELETON_HIERARCHY[spec.parent].append(spec.name)

LANDMARK_MAP = {spec.name: list(spec.landmarks) for spec in JOINT_SPECS}
REST_POSE_OFFSETS = {spec.name: np.array(spec.offset, dtype=float) for spec in JOINT_SPECS}

BONE_CONNECTIONS = tuple(
    (spec.parent, spec.name) for spec in JOINT_SPECS if spec.parent is not None
)
