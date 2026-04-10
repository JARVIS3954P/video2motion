import numpy as np
import io
from .config import SKELETON_HIERARCHY, REST_POSE_OFFSETS


class BVHExporter:
    def __init__(self, output_path=None, fps=30):
        """
        Args:
            output_path (str | None): If given, export() writes to disk.
                                      Pass None to use get_bvh_string() only.
            fps (float): Frames per second of the source video.
        """
        self.output_path = output_path
        self.fps = fps
        self.frames = []          # list of (root_position, rotations)
        self.skeleton = SKELETON_HIERARCHY
        self.offsets = REST_POSE_OFFSETS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_frame(self, root_position, rotations):
        """
        Add a frame of motion data.

        Args:
            root_position (np.array): [x, y, z] position of Hips.
            rotations (dict): {joint_name: [z_deg, x_deg, y_deg]}
        """
        self.frames.append((root_position, rotations))

    def get_bvh_string(self):
        """Return BVH file content as a string (no disk I/O)."""
        buf = io.StringIO()
        self._write_bvh(buf)
        return buf.getvalue()

    def export(self):
        """Write the BVH file to disk."""
        if not self.output_path:
            raise ValueError("output_path was not set. Use get_bvh_string() instead.")
        with open(self.output_path, 'w') as f:
            self._write_bvh(f)
        print(f"BVH exported to: {self.output_path}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_bvh(self, f):
        """Write complete BVH content to a file-like object."""
        f.write("HIERARCHY\n")
        self._write_hierarchy(f, "Hips", 0)

        f.write("MOTION\n")
        f.write(f"Frames: {len(self.frames)}\n")
        f.write(f"Frame Time: {1.0 / self.fps:.6f}\n")

        for root_pos, rotations in self.frames:
            self._write_frame_data(f, root_pos, rotations)

    def _write_hierarchy(self, f, joint_name, level):
        indent = "  " * level

        offset = self.offsets.get(joint_name, np.zeros(3))

        if joint_name == "Hips":
            f.write(f"{indent}ROOT {joint_name}\n")
        else:
            f.write(f"{indent}JOINT {joint_name}\n")

        f.write(f"{indent}{{\n")
        f.write(f"{indent}  OFFSET {offset[0]:.6f} {offset[1]:.6f} {offset[2]:.6f}\n")

        children = self.skeleton.get(joint_name, [])

        if joint_name == "Hips":
            # Root: position + rotation channels
            f.write(f"{indent}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
        else:
            # All non-root joints (including leaves) have rotation channels
            f.write(f"{indent}  CHANNELS 3 Zrotation Xrotation Yrotation\n")

        if children:
            for child in children:
                self._write_hierarchy(f, child, level + 1)
        else:
            # End Site block — required for valid BVH leaf joints
            f.write(f"{indent}  End Site\n")
            f.write(f"{indent}  {{\n")
            # Small non-zero offset so the bone has visible length
            f.write(f"{indent}    OFFSET 0.0 0.05 0.0\n")
            f.write(f"{indent}  }}\n")

        f.write(f"{indent}}}\n")

    def _write_frame_data(self, f, root_pos, rotations):
        line_data = []
        self._collect_frame_data_recursive("Hips", root_pos, rotations, line_data)
        f.write(" ".join(line_data) + "\n")

    def _collect_frame_data_recursive(self, joint_name, root_pos, rotations, line_data):
        rot = rotations.get(joint_name, [0.0, 0.0, 0.0])

        if joint_name == "Hips":
            # POS POS POS ZROT XROT YROT
            line_data.extend([
                f"{root_pos[0]:.6f}", f"{root_pos[1]:.6f}", f"{root_pos[2]:.6f}",
                f"{rot[0]:.6f}", f"{rot[1]:.6f}", f"{rot[2]:.6f}"
            ])
        else:
            # Non-root joints: write rotation channels (including leaves)
            line_data.extend([
                f"{rot[0]:.6f}", f"{rot[1]:.6f}", f"{rot[2]:.6f}"
            ])

        children = self.skeleton.get(joint_name, [])
        for child in children:
            self._collect_frame_data_recursive(child, root_pos, rotations, line_data)
