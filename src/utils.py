import numpy as np
import math

def normalize_vector(v):
    """Normalize a vector to unit length."""
    norm = np.linalg.norm(v)
    if norm < 1e-6:
        return v
    return v / norm

def rotation_matrix_from_vectors(vec1, vec2):
    """
    Calculate the rotation matrix that rotates vec1 to align with vec2.
    Using Rodrigues' rotation formula.
    """
    u = normalize_vector(vec1)
    v = normalize_vector(vec2)
    
    # If vectors are already aligned
    if np.allclose(u, v):
        return np.eye(3)
        
    # If vectors are opposite
    if np.allclose(u, -v):
        # Rotate 180 degrees around any orthogonal axis
        # Find orthogonal axis
        axis = np.cross(u, np.array([1, 0, 0]))
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(u, np.array([0, 1, 0]))
        axis = normalize_vector(axis)
        return rotation_matrix_from_axis_angle(axis, np.pi)
        
    # Standard case
    cross_prod = np.cross(u, v)
    dot_prod = np.dot(u, v)
    
    s = np.linalg.norm(cross_prod)
    
    # Handle numerical instability for very close vectors not caught by allclose
    if s < 1e-6:
        if dot_prod > 0:
            return np.eye(3)
        else:
            # Opposite
            axis = np.cross(u, np.array([1, 0, 0]))
            if np.linalg.norm(axis) < 1e-6:
                axis = np.cross(u, np.array([0, 1, 0]))
            axis = normalize_vector(axis)
            return rotation_matrix_from_axis_angle(axis, np.pi)

    # Skew-symmetric cross-product matrix
    K = np.array([
        [0, -cross_prod[2], cross_prod[1]],
        [cross_prod[2], 0, -cross_prod[0]],
        [-cross_prod[1], cross_prod[0], 0]
    ])
    
    R = np.eye(3) + K + K @ K * ((1 - dot_prod) / (s**2))
    return R

def rotation_matrix_from_axis_angle(axis, angle):
    """Create a rotation matrix from an axis and an angle (radians)."""
    c = np.cos(angle)
    s = np.sin(angle)
    t = 1 - c
    x, y, z = normalize_vector(axis)
    
    R = np.array([
        [t*x*x + c,   t*x*y - z*s, t*x*z + y*s],
        [t*x*y + z*s, t*y*y + c,   t*y*z - x*s],
        [t*x*z - y*s, t*y*z + x*s, t*z*z + c]
    ])
    return R

def rotation_matrix_to_euler(R, order='ZXY'):
    """
    Convert rotation matrix to Euler angles (degrees).
    BVH usually uses ZXY or ZYX order. 
    Here implementing ZXY (common for BVH, checks might be needed).
    
    Note: 'ZXY' means rotate around Y, then X, then Z (GLOBAL AXES usually)
    or intrinsic Z, then X, then Y?
    BVH standard is usually intrinsic rotations.
    Code below implements intrinsic ZXY.
    """
    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    
    singular = sy < 1e-6
    
    if not singular:
        if order == 'ZXY':
            x = math.asin(R[2, 1])
            y = math.atan2(-R[2, 0], R[2, 2])
            z = math.atan2(-R[0, 1], R[1, 1])
        elif order == 'ZYX': 
             x = math.atan2(R[2, 1], R[2, 2])
             y = math.asin(-R[2, 0])
             z = math.atan2(R[1, 0], R[0, 0])
        else:
            raise NotImplementedError(f"Order {order} not implemented.")
    else:
        # Gimbal lock support is basic here
        if order == 'ZXY':
            x = math.asin(R[2, 1])
            y = math.atan2(-R[2, 0], R[2, 2])
            z = 0
        elif order == 'ZYX':
             x = math.atan2(R[2, 1], R[2, 2])
             y = math.asin(-R[2, 0])
             z = 0
        else:
            raise NotImplementedError
            
    return np.degrees(np.array([z, x, y])) # Note: Return order matches channel order in BVH often? 
    # Actually, if order is ZXY, we return [Z, X, Y]. 
    
    # Wait, usually we need to match the BVH channels.
    # If BVH says "CHANNELS 3 Zrotation Xrotation Yrotation", we return [Z, X, Y].
