import numpy as np
from .config import SKELETON_HIERARCHY, LANDMARK_MAP, REST_POSE_OFFSETS
from .utils import normalize_vector, rotation_matrix_from_vectors, rotation_matrix_to_euler

class MotionCalculator:
    def __init__(self):
        self.skeleton = SKELETON_HIERARCHY
        self.landmark_map = LANDMARK_MAP
        self.rest_offsets = REST_POSE_OFFSETS

    def calculate_joint_angles(self, frame_landmarks):
        """
        Calculate joint rotations for a single frame.
        
        Args:
            frame_landmarks (np.array): Smoothed, normalized landmarks (33, 4).
            
        Returns:
            rotations (dict): {joint_name: [z_deg, x_deg, y_deg]}
            root_position (np.array): [x, y, z] for Hips
        """
        rotations = {}
        
        # Get Root Position (Hips)
        # Note: input landmarks are already hip-centered at (0,0,0) usually if normalized.
        # But for BVH we might want the absolute movement if we didn't center them perfectly per frame.
        # If we centered them per frame, root pos is always 0,0,0, which removes root motion.
        # Ideally, we want root motion. 
        # The PoseNormalizer centered them. so root is 0.
        # To get root motion, we should have kept the hip center BEFORE normalization 
        # or we accept that this is in-place animation. (Usually preferred for game engines).
        # Let's assume in-place for now (0,0,0), unless we change normalization strategy.
        root_position = np.array([0.0, 0.0, 0.0]) 

        # We need to compute global positions of skeleton joints from landmarks
        # The landmarks map to joints.
        skeleton_positions = {}
        for joint, indices in self.landmark_map.items():
            if not indices:
                skeleton_positions[joint] = np.zeros(3) # End site or similar
                continue
            
             # Get centroids of indices
            points = frame_landmarks[indices, :3]
            skeleton_positions[joint] = np.mean(points, axis=0)

        # Calculate Rotations
        # We process hierarchically? 
        # Actually, for each bone, we compare its vector (Parent -> Child) in current frame
        # vs. the vector in Rest Pose.
        
        # NOTE: This is a simplified analytic solver. 
        # A full IK solver is better but complex.
        # Here we use "direction matching": rotate parent to align rest-vector to target-vector.
        
        # Problem: A single vector alignment leaves a degree of freedom (twist).
        # We need a secondary constraint (Up vector) or rely on parent orientation.
        
        # For this implementation, we will act "globally" for simplicity first, 
        # then convert to local if needed. 
        # BVH stores LOCAL rotations relative to parent.
        
        # Let's iterate through the hierarchy.
        # We need global orientations of parents to compute local rotations.
        
        global_orientations = {'World': np.eye(3)} # Identity matrix for world
        
        # Simple recursion helper
        self._compute_joint_rotation('Hips', 'World', skeleton_positions, rotations, global_orientations)
        
        return rotations, root_position

    def _compute_joint_rotation(self, joint_name, parent_name, skeleton_positions, rotations, global_orientations):
        
        children = self.skeleton.get(joint_name, [])
        if not children:
            # End Site, no rotation needed usually
            rotations[joint_name] = [0.0, 0.0, 0.0]
            global_orientations[joint_name] = global_orientations[parent_name]
            return

        # We primarily look at the first child to determine the main bone vector.
        # e.g. Hips -> Spine. 
        # For Hips, we have multiple children (Spine, Legs).
        # We usually define Hips rotation based on the Hips-Spine vector and Hips-Legs plane.
        
        # Case 1: Hips (Root)
        if joint_name == 'Hips':
            # Define Forward and Up vectors for Hips
            # Up: Hips -> Spine (or mid-spine)
            # Right: LeftHip -> RightHip
            
            # Using landmark positions directly
            hip_center = skeleton_positions['Hips']
            spine_pos = skeleton_positions['Spine'] # or Spine1
            left_hip = skeleton_positions['LeftUpLeg'] # Approximation
            right_hip = skeleton_positions['RightUpLeg']
            
            # Target vectors
            target_up = normalize_vector(spine_pos - hip_center)
            target_right = normalize_vector(right_hip - left_hip)
            target_forward = normalize_vector(np.cross(target_right, target_up))
            
            # Re-orthogonalize Right
            target_right = np.cross(target_up, target_forward)
            
            # Construct Rotation Matrix (Global)
            # [Right, Up, Forward] as columns? Depends on coord system.
            # OpenGL: X=Right, Y=Up, Z=Back (or Forward). 
            # BVH often Y-Up.
            # Let's assume standard basis: X=1,0,0 Y=0,1,0 Z=0,0,1
            # We want to map Basis to Target.
            
            R_global = np.column_stack((target_right, target_up, target_forward))
            
            # But wait, is our Rest Pose aligned with World?
            # Creating a matrix from scratch assumes Rest Pose was Identity.
            # If Rest Pose has rotations, we need to account for them.
            # Assuming T-Pose is our Identity reference.
            
            global_orientations[joint_name] = R_global
            
            # Local rotation for Hips is same as Global (since parent is World)
            rotations[joint_name] = rotation_matrix_to_euler(R_global, 'ZXY')


        # Case 2: Limbs / Spine
        else:
             # Basic approach: Align parent-child vector
             first_child = children[0]
             
             # Current Vector in Global Space
             curr_vec = skeleton_positions[first_child] - skeleton_positions[joint_name]
             curr_dir = normalize_vector(curr_vec)
             
             # Rest Vector in Local Space (from config)
             # We assume rest pose is T-Pose.
             # e.g. RightArm rest vector is (-1, 0, 0) relative to Shoulder.
             rest_offset = self.rest_offsets[first_child] # Vector from joint to child in rest pose
             rest_dir = normalize_vector(rest_offset)
             
             # We need to rotate the Rest Vector (Local) by the Parent's Global Orientation
             # to compare it with the Current Vector (Global).
             # R_parent * R_local * rest_dir = curr_dir
             # R_local * rest_dir = inv(R_parent) * curr_dir
             
             parent_global_R = global_orientations[parent_name]
             target_local_vec = np.linalg.inv(parent_global_R) @ curr_dir
             
             # Calculate R_local that rotates rest_dir to target_local_vec
             R_local = rotation_matrix_from_vectors(rest_dir, target_local_vec)
             
             rotations[joint_name] = rotation_matrix_to_euler(R_local, 'ZXY')
             
             # Update Global Orientation for this joint
             # Global = ParentGlobal * Local
             global_orientations[joint_name] = parent_global_R @ R_local

        # Recurse
        for child in children:
            self._compute_joint_rotation(child, joint_name, skeleton_positions, rotations, global_orientations)
