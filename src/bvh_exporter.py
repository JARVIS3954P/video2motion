import numpy as np
from .config import SKELETON_HIERARCHY, REST_POSE_OFFSETS

class BVHExporter:
    def __init__(self, output_path, fps=30):
        self.output_path = output_path
        self.fps = fps
        self.frames = []
        self.joint_names = [] # To keep track of traversal order
        self.skeleton = SKELETON_HIERARCHY
        self.offsets = REST_POSE_OFFSETS

    def add_frame(self, root_position, rotations):
        """
        Add a frame of motion data.
        
        Args:
            root_position (np.array): [x, y, z] position of Hips.
            rotations (dict): {joint_name: [z_deg, x_deg, y_deg]}
        """
        self.frames.append((root_position, rotations))

    def export(self):
        """Write the BVH file."""
        with open(self.output_path, 'w') as f:
            f.write("HIERARCHY\n")
            self._write_hierarchy(f, "Hips", 0)
            
            f.write("MOTION\n")
            f.write(f"Frames: {len(self.frames)}\n")
            f.write(f"Frame Time: {1.0/self.fps:.6f}\n")
            
            for root_pos, rotations in self.frames:
                self._write_frame_data(f, root_pos, rotations)
                
        print(f"BVH exported to: {self.output_path}")

    def _write_hierarchy(self, f, joint_name, level):
        indent = "  " * level
        
        offset = self.offsets.get(joint_name, np.zeros(3))
        
        if joint_name == "Hips":
            f.write(f"{indent}ROOT {joint_name}\n")
        else:
            f.write(f"{indent}JOINT {joint_name}\n")
            
        f.write(f"{indent}{{\n")
        f.write(f"{indent}  OFFSET {offset[0]:.6f} {offset[1]:.6f} {offset[2]:.6f}\n")
        
        if joint_name == "Hips":
             f.write(f"{indent}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
        elif not self.skeleton.get(joint_name): # End Site
             # Usually End Site doesn't have channels, but here we treat leaf joints as joints?
             # Standard BVH has "End Site" block for leaves.
             pass 
        else:
             f.write(f"{indent}  CHANNELS 3 Zrotation Xrotation Yrotation\n")

        # Children
        children = self.skeleton.get(joint_name, [])
        if children:
            for child in children:
                self._write_hierarchy(f, child, level + 1)
        else:
            # Tip / End Site
            # We need to define an offset for the end site.
            # Usually we don't track the tip, so we make up a small offset or use a standard one.
            f.write(f"{indent}  End Site\n")
            f.write(f"{indent}  {{\n")
            # Heuristic end site offset (e.g. length of hand/foot)
            # Just verify direction. 
            # Or use (0,0,0) if we don't care about visual bones of the tips
            f.write(f"{indent}    OFFSET 0.0 0.0 0.0\n") 
            f.write(f"{indent}  }}\n")

        f.write(f"{indent}}}\n")
        
        if joint_name not in self.joint_names:
            self.joint_names.append(joint_name)

    def _write_frame_data(self, f, root_pos, rotations):
        line_data = []
        
        # Traversal order must match hierarchy writing order
        # We can re-traverse or store the order.
        # Let's re-traverse to be safe and simple.
        
        stack = ["Hips"]
        processed = []
        
        # This needs to match the depth-first recursion of _write_hierarchy exactly.
        # So we should use a helper generator or just the same recursion logic.
        
        self._collect_frame_data_recursive(f, "Hips", root_pos, rotations, line_data)
        
        f.write(" ".join(line_data) + "\n")
        
    def _collect_frame_data_recursive(self, f, joint_name, root_pos, rotations, line_data):
        
        rot = rotations.get(joint_name, [0.0, 0.0, 0.0])
        
        if joint_name == "Hips":
            # POS POS POS ZROT XROT YROT
            line_data.extend([
                f"{root_pos[0]:.6f}", f"{root_pos[1]:.6f}", f"{root_pos[2]:.6f}",
                f"{rot[0]:.6f}", f"{rot[1]:.6f}", f"{rot[2]:.6f}"
            ])
        else:
            # ZROT XROT YROT
            line_data.extend([
                f"{rot[0]:.6f}", f"{rot[1]:.6f}", f"{rot[2]:.6f}"
            ])
            
        children = self.skeleton.get(joint_name, [])
        for child in children:
            self._collect_frame_data_recursive(f, child, root_pos, rotations, line_data)
