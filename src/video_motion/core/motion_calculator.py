import numpy as np

from ..config import (
    LANDMARK_MAP,
    MP_LEFT_ANKLE,
    MP_LEFT_ELBOW,
    MP_LEFT_FOOT_INDEX,
    MP_LEFT_HEEL,
    MP_LEFT_HIP,
    MP_LEFT_INDEX,
    MP_LEFT_KNEE,
    MP_LEFT_PINKY,
    MP_LEFT_SHOULDER,
    MP_LEFT_THUMB,
    MP_LEFT_WRIST,
    MP_NOSE,
    MP_RIGHT_ANKLE,
    MP_RIGHT_ELBOW,
    MP_RIGHT_FOOT_INDEX,
    MP_RIGHT_HEEL,
    MP_RIGHT_HIP,
    MP_RIGHT_INDEX,
    MP_RIGHT_KNEE,
    MP_RIGHT_PINKY,
    MP_RIGHT_SHOULDER,
    MP_RIGHT_THUMB,
    MP_RIGHT_WRIST,
    REST_POSE_OFFSETS,
    SKELETON_HIERARCHY,
)
from ..utils.utils import normalize_vector, rotation_matrix_to_euler


def _safe_inverse(matrix):
    try:
        return np.linalg.inv(matrix)
    except np.linalg.LinAlgError:
        return np.eye(3)


class MotionCalculator:
    def __init__(self):
        self.skeleton = SKELETON_HIERARCHY
        self.landmark_map = LANDMARK_MAP
        self.rest_offsets = REST_POSE_OFFSETS
        self.rest_global = {}
        self.rest_local = {}

    def _point(self, landmarks, index):
        return landmarks[index, :3]

    def _skeleton_positions(self, landmarks):
        positions = {}
        for joint, indices in self.landmark_map.items():
            if indices:
                positions[joint] = np.mean(landmarks[indices, :3], axis=0)
            else:
                positions[joint] = np.zeros(3)

        hip_center = positions["Hips"]
        shoulder_center = np.mean(landmarks[[MP_LEFT_SHOULDER, MP_RIGHT_SHOULDER], :3], axis=0)
        spine_vec = shoulder_center - hip_center
        positions["Spine"] = hip_center + spine_vec * 0.30
        positions["Spine1"] = hip_center + spine_vec * 0.58
        positions["Spine2"] = hip_center + spine_vec * 0.84
        positions["Neck"] = shoulder_center + np.array([0.0, 0.06, 0.0])
        return positions

    def _orthonormal(self, x_axis=None, y_axis=None, z_axis=None):
        x = normalize_vector(np.array(x_axis, dtype=float)) if x_axis is not None else None
        y = normalize_vector(np.array(y_axis, dtype=float)) if y_axis is not None else None
        z = normalize_vector(np.array(z_axis, dtype=float)) if z_axis is not None else None

        if x is None and y is not None and z is not None:
            x = normalize_vector(np.cross(y, z))
        if y is None and z is not None and x is not None:
            y = normalize_vector(np.cross(z, x))
        if z is None and x is not None and y is not None:
            z = normalize_vector(np.cross(x, y))

        if x is None or np.linalg.norm(x) < 1e-6:
            x = np.array([1.0, 0.0, 0.0])
        if y is None or np.linalg.norm(y) < 1e-6:
            y = np.array([0.0, 1.0, 0.0])
        z = normalize_vector(np.cross(x, y))
        if np.linalg.norm(z) < 1e-6:
            z = normalize_vector(np.cross(x, [0.0, 0.0, 1.0]))
        if np.linalg.norm(z) < 1e-6:
            z = np.array([0.0, 0.0, 1.0])
        y = normalize_vector(np.cross(z, x))
        return np.column_stack((normalize_vector(x), y, z))

    def _frame_from_primary(self, primary, child_name, secondary=None):
        offset = self.rest_offsets.get(child_name, np.array([0.0, 1.0, 0.0]))
        axis_index = int(np.argmax(np.abs(offset)))
        axis_sign = 1.0 if offset[axis_index] >= 0 else -1.0

        primary_dir = normalize_vector(primary)
        if np.linalg.norm(primary_dir) < 1e-6:
            primary_dir = normalize_vector(offset)

        axes = [None, None, None]
        axes[axis_index] = primary_dir * axis_sign

        helper = normalize_vector(secondary) if secondary is not None else np.array([0.0, 0.0, 1.0])
        if np.linalg.norm(helper) < 1e-6 or abs(np.dot(helper, axes[axis_index])) > 0.92:
            helper = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(helper, axes[axis_index])) > 0.92:
            helper = np.array([1.0, 0.0, 0.0])

        if axis_index == 0:
            axes[2] = normalize_vector(helper - np.dot(helper, axes[0]) * axes[0])
            axes[1] = normalize_vector(np.cross(axes[2], axes[0]))
        elif axis_index == 1:
            axes[0] = normalize_vector(helper - np.dot(helper, axes[1]) * axes[1])
            axes[2] = normalize_vector(np.cross(axes[0], axes[1]))
        else:
            axes[0] = normalize_vector(helper - np.dot(helper, axes[2]) * axes[2])
            axes[1] = normalize_vector(np.cross(axes[2], axes[0]))

        return self._orthonormal(axes[0], axes[1], axes[2])

    def _hip_frame(self, landmarks):
        left_hip = self._point(landmarks, MP_LEFT_HIP)
        right_hip = self._point(landmarks, MP_RIGHT_HIP)
        hip_center = (left_hip + right_hip) / 2.0
        knee_center = (self._point(landmarks, MP_LEFT_KNEE) + self._point(landmarks, MP_RIGHT_KNEE)) / 2.0
        return self._orthonormal(x_axis=left_hip - right_hip, y_axis=hip_center - knee_center)

    def _chest_frame(self, landmarks):
        left_shoulder = self._point(landmarks, MP_LEFT_SHOULDER)
        right_shoulder = self._point(landmarks, MP_RIGHT_SHOULDER)
        shoulder_center = (left_shoulder + right_shoulder) / 2.0
        hip_center = (self._point(landmarks, MP_LEFT_HIP) + self._point(landmarks, MP_RIGHT_HIP)) / 2.0
        return self._orthonormal(x_axis=left_shoulder - right_shoulder, y_axis=shoulder_center - hip_center)

    def _blend_matrix(self, a, b, t):
        blended = a * (1.0 - t) + b * t
        u, _, vh = np.linalg.svd(blended)
        return u @ vh

    def _hand_frame(self, landmarks, side):
        if side == "Right":
            wrist = self._point(landmarks, MP_RIGHT_WRIST)
            index = self._point(landmarks, MP_RIGHT_INDEX)
            pinky = self._point(landmarks, MP_RIGHT_PINKY)
            thumb = self._point(landmarks, MP_RIGHT_THUMB)
            primary = ((index + pinky) / 2.0) - wrist
        else:
            wrist = self._point(landmarks, MP_LEFT_WRIST)
            index = self._point(landmarks, MP_LEFT_INDEX)
            pinky = self._point(landmarks, MP_LEFT_PINKY)
            thumb = self._point(landmarks, MP_LEFT_THUMB)
            primary = ((index + pinky) / 2.0) - wrist
        return self._frame_from_primary(primary, f"{side}Index1", thumb - pinky)

    def _foot_frame(self, landmarks, side):
        if side == "Right":
            ankle = self._point(landmarks, MP_RIGHT_ANKLE)
            toe = self._point(landmarks, MP_RIGHT_FOOT_INDEX)
            heel = self._point(landmarks, MP_RIGHT_HEEL)
        else:
            ankle = self._point(landmarks, MP_LEFT_ANKLE)
            toe = self._point(landmarks, MP_LEFT_FOOT_INDEX)
            heel = self._point(landmarks, MP_LEFT_HEEL)
        return self._frame_from_primary(toe - ankle, f"{side}ToeBase", heel - ankle)

    def _global_orientations(self, landmarks, positions):
        hips = self._hip_frame(landmarks)
        chest = self._chest_frame(landmarks)
        orientations = {
            "Hips": hips,
            "Spine": self._blend_matrix(hips, chest, 0.35),
            "Spine1": self._blend_matrix(hips, chest, 0.65),
            "Spine2": chest,
            "Neck": chest,
            "Head": self._frame_from_primary(
                self._point(landmarks, MP_NOSE) - positions["Neck"],
                "HeadEnd",
                chest[:, 0],
            ),
            "RightShoulder": chest,
            "LeftShoulder": chest,
        }

        specs = (
            ("RightArm", MP_RIGHT_SHOULDER, MP_RIGHT_ELBOW, MP_RIGHT_WRIST),
            ("RightForeArm", MP_RIGHT_ELBOW, MP_RIGHT_WRIST, MP_RIGHT_INDEX),
            ("LeftArm", MP_LEFT_SHOULDER, MP_LEFT_ELBOW, MP_LEFT_WRIST),
            ("LeftForeArm", MP_LEFT_ELBOW, MP_LEFT_WRIST, MP_LEFT_INDEX),
            ("RightUpLeg", MP_RIGHT_HIP, MP_RIGHT_KNEE, MP_RIGHT_ANKLE),
            ("RightLeg", MP_RIGHT_KNEE, MP_RIGHT_ANKLE, MP_RIGHT_FOOT_INDEX),
            ("LeftUpLeg", MP_LEFT_HIP, MP_LEFT_KNEE, MP_LEFT_ANKLE),
            ("LeftLeg", MP_LEFT_KNEE, MP_LEFT_ANKLE, MP_LEFT_FOOT_INDEX),
        )
        for name, start, mid, end in specs:
            orientations[name] = self._frame_from_primary(
                self._point(landmarks, mid) - self._point(landmarks, start),
                self.skeleton[name][0],
                self._point(landmarks, end) - self._point(landmarks, mid),
            )

        orientations["RightHand"] = self._hand_frame(landmarks, "Right")
        orientations["LeftHand"] = self._hand_frame(landmarks, "Left")
        orientations["RightFoot"] = self._foot_frame(landmarks, "Right")
        orientations["LeftFoot"] = self._foot_frame(landmarks, "Left")
        orientations["RightToeBase"] = orientations["RightFoot"]
        orientations["LeftToeBase"] = orientations["LeftFoot"]

        finger_specs = (
            ("RightIndex1", MP_RIGHT_WRIST, MP_RIGHT_INDEX),
            ("RightPinky1", MP_RIGHT_WRIST, MP_RIGHT_PINKY),
            ("RightThumb1", MP_RIGHT_WRIST, MP_RIGHT_THUMB),
            ("LeftIndex1", MP_LEFT_WRIST, MP_LEFT_INDEX),
            ("LeftPinky1", MP_LEFT_WRIST, MP_LEFT_PINKY),
            ("LeftThumb1", MP_LEFT_WRIST, MP_LEFT_THUMB),
        )
        for name, start, end in finger_specs:
            orientations[name] = self._frame_from_primary(
                self._point(landmarks, end) - self._point(landmarks, start),
                self.skeleton[name][0],
                orientations["RightHand" if name.startswith("Right") else "LeftHand"][:, 2],
            )

        for joint, children in self.skeleton.items():
            if joint in orientations:
                continue
            parent = next((p for p, cs in self.skeleton.items() if joint in cs), None)
            orientations[joint] = orientations.get(parent, np.eye(3))
        return orientations

    def calibrate(self, frame_0_landmarks):
        positions = self._skeleton_positions(frame_0_landmarks)
        self.rest_global = self._global_orientations(frame_0_landmarks, positions)
        self.rest_local = {}
        self._collect_rest_local("Hips", "World")

    def _collect_rest_local(self, joint, parent):
        parent_global = np.eye(3) if parent == "World" else self.rest_global[parent]
        self.rest_local[joint] = _safe_inverse(parent_global) @ self.rest_global[joint]
        for child in self.skeleton.get(joint, []):
            self._collect_rest_local(child, joint)

    def calculate_joint_angles(self, frame_landmarks, root_position=None):
        if not self.rest_global:
            self.calibrate(frame_landmarks)

        positions = self._skeleton_positions(frame_landmarks)
        current_global = self._global_orientations(frame_landmarks, positions)
        rotations = {}
        self._collect_rotations("Hips", "World", current_global, rotations)
        root_position = np.array(root_position if root_position is not None else [0.0, 0.0, 0.0])
        return rotations, root_position

    def _collect_rotations(self, joint, parent, current_global, rotations):
        current_joint = current_global.get(joint, self.rest_global.get(joint, np.eye(3)))
        if parent == "World":
            current_local = current_joint
        else:
            current_parent = current_global.get(parent, self.rest_global.get(parent, np.eye(3)))
            current_local = _safe_inverse(current_parent) @ current_joint

        rest_local = self.rest_local.get(joint, np.eye(3))
        rotations[joint] = rotation_matrix_to_euler(current_local @ _safe_inverse(rest_local), "ZXY")

        for child in self.skeleton.get(joint, []):
            self._collect_rotations(child, joint, current_global, rotations)
