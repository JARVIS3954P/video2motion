import numpy as np
from scipy.spatial.transform import Rotation as R_scipy

def normalize_vector(v):
    """Normalize a vector to unit length."""
    norm = np.linalg.norm(v)
    if norm < 1e-6:
        return v
    return v / norm

def rotation_matrix_from_vectors(vec1, vec2):
    """
    Calculate the rotation matrix that rotates vec1 to align with vec2.
    """
    u = normalize_vector(vec1)
    v = normalize_vector(vec2)
    
    if np.linalg.norm(u) < 1e-6 or np.linalg.norm(v) < 1e-6:
        return np.eye(3)
        
    if np.allclose(u, v):
        return np.eye(3)
        
    if np.allclose(u, -v):
        axis = np.cross(u, np.array([1, 0, 0]))
        if np.linalg.norm(axis) < 1e-6:
            axis = np.cross(u, np.array([0, 1, 0]))
        axis = normalize_vector(axis)
        r = R_scipy.from_rotvec(np.pi * axis)
        return r.as_matrix()
        
    cross_prod = np.cross(u, v)
    dot_prod = np.dot(u, v)
    s = np.linalg.norm(cross_prod)
    
    if s < 1e-6:
        if dot_prod > 0:
            return np.eye(3)
        else:
            axis = np.cross(u, np.array([1, 0, 0]))
            if np.linalg.norm(axis) < 1e-6:
                axis = np.cross(u, np.array([0, 1, 0]))
            axis = normalize_vector(axis)
            r = R_scipy.from_rotvec(np.pi * axis)
            return r.as_matrix()

    K = np.array([
        [0, -cross_prod[2], cross_prod[1]],
        [cross_prod[2], 0, -cross_prod[0]],
        [-cross_prod[1], cross_prod[0], 0]
    ])
    
    R = np.eye(3) + K + K @ K * ((1 - dot_prod) / (s**2))
    return R

def rotation_matrix_to_euler(R_mat, order='ZXY'):
    """
    Convert rotation matrix to Euler angles (degrees) using SciPy.
    Intrinsic rotations are denoted by lowercase in SciPy (e.g., 'zxy').
    """
    try:
        r = R_scipy.from_matrix(R_mat)
        return r.as_euler(order.lower(), degrees=True)
    except Exception:
        return np.array([0.0, 0.0, 0.0])