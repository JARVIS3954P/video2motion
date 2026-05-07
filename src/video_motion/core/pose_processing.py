import numpy as np
from scipy.signal import savgol_filter

from ..config import MP_LEFT_HIP, MP_RIGHT_HIP


def _odd_window(requested: int, frame_count: int, polyorder: int) -> int | None:
    if frame_count <= polyorder + 1:
        return None

    window = min(int(requested), frame_count)
    if window % 2 == 0:
        window -= 1
    min_window = polyorder + 2
    if min_window % 2 == 0:
        min_window += 1
    window = max(window, min_window)
    if window > frame_count:
        window = frame_count if frame_count % 2 == 1 else frame_count - 1
    return window if window > polyorder else None


class PoseNormalizer:
    def hip_center(self, landmarks):
        left_hip = landmarks[MP_LEFT_HIP, :3]
        right_hip = landmarks[MP_RIGHT_HIP, :3]
        return (left_hip + right_hip) / 2.0

    def normalize_pose(self, landmarks):
        if landmarks is None:
            return None

        norm_landmarks = landmarks.copy()
        norm_landmarks[:, :3] -= self.hip_center(landmarks)
        return norm_landmarks


class TemporalSmoother:
    def __init__(self, window_length=5, polyorder=2):
        self.window_length = window_length
        self.polyorder = polyorder
        self.pose_buffer = []

    def update(self, landmarks):
        self.pose_buffer.append(landmarks)
        return landmarks

    def fill_missing(self, all_landmarks):
        valid_indices = [i for i, item in enumerate(all_landmarks) if item is not None]
        if not valid_indices:
            return np.empty((0, 33, 4), dtype=np.float32)

        data = np.zeros((len(all_landmarks), 33, 4), dtype=np.float32)
        valid_data = np.array([all_landmarks[i] for i in valid_indices], dtype=np.float32)
        source_x = np.array(valid_indices, dtype=float)
        target_x = np.arange(len(all_landmarks), dtype=float)

        for joint in range(33):
            for coord in range(4):
                data[:, joint, coord] = np.interp(
                    target_x,
                    source_x,
                    valid_data[:, joint, coord],
                )

        return data[valid_indices[0] : valid_indices[-1] + 1]

    def smooth_all(self, all_landmarks):
        data = self.fill_missing(all_landmarks)
        if data.size == 0:
            return data

        frames, joints, _ = data.shape
        window = _odd_window(self.window_length, frames, self.polyorder)
        if window is None:
            return data

        smoothed = data.copy()
        for joint in range(joints):
            for coord in range(3):
                smoothed[:, joint, coord] = savgol_filter(
                    data[:, joint, coord],
                    window,
                    min(self.polyorder, window - 1),
                    mode="interp",
                )
        return smoothed

    def smooth_vectors(self, vectors):
        data = np.array(vectors, dtype=float)
        if len(data) == 0:
            return data

        window = _odd_window(self.window_length, len(data), self.polyorder)
        if window is None:
            return data

        smoothed = data.copy()
        for coord in range(data.shape[1]):
            smoothed[:, coord] = savgol_filter(
                data[:, coord],
                window,
                min(self.polyorder, window - 1),
                mode="interp",
            )
        return smoothed

    def smooth_rotations(self, rotations):
        if not rotations:
            return rotations

        window = _odd_window(self.window_length, len(rotations), 2)
        if window is None:
            return rotations

        joints = list(rotations[0].keys())
        smoothed = [dict(frame) for frame in rotations]
        for joint in joints:
            angles = np.array([frame[joint] for frame in rotations], dtype=float)
            unwrapped = np.unwrap(np.radians(angles), axis=0)
            for axis in range(3):
                unwrapped[:, axis] = savgol_filter(
                    unwrapped[:, axis],
                    window,
                    2,
                    mode="interp",
                )
            degrees = np.degrees(unwrapped)
            for frame_index in range(len(smoothed)):
                smoothed[frame_index][joint] = degrees[frame_index]

        return smoothed
