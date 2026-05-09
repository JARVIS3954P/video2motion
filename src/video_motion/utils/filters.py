import math
import numpy as np


def smoothing_factor(t_e, cutoff):
    r = 2 * math.pi * cutoff * t_e
    return r / (r + 1)


def exponential_smoothing(a, x, x_prev):
    return a * x + (1 - a) * x_prev


class BatchedOneEuroFilter:
    """
    Offline (batched) implementation of the 1 Euro Filter.
    Applies the filter over an entire numpy array (frames, ...).
    """
    def __init__(self, min_cutoff=1.0, beta=0.005, d_cutoff=1.0, fps=30.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.fps = fps

    def __call__(self, data):
        data = np.array(data, dtype=float)
        if len(data) <= 1:
            return data

        t_e = 1.0 / self.fps
        a_d = smoothing_factor(t_e, self.d_cutoff)
        
        smoothed = np.zeros_like(data)
        smoothed[0] = data[0]
        
        x_prev = data[0].copy()
        dx_prev = np.zeros_like(data[0])
        
        for i in range(1, len(data)):
            x = data[i]
            dx = (x - x_prev) / t_e
            dx_hat = exponential_smoothing(a_d, dx, dx_prev)
            
            # Use norm of velocity for adaptive cutoff if dealing with coordinates
            if data.ndim > 1:
                if data.ndim == 3: # (frames, joints, 3)
                    speed = np.linalg.norm(dx_hat, axis=-1, keepdims=True)
                elif data.ndim == 2: # (frames, 3)
                    speed = np.linalg.norm(dx_hat, axis=-1, keepdims=True)
                else:
                    speed = np.abs(dx_hat)
            else:
                speed = np.abs(dx_hat)
                
            cutoff = self.min_cutoff + self.beta * speed
            a = smoothing_factor(t_e, cutoff)
            x_hat = exponential_smoothing(a, x, x_prev)
            
            smoothed[i] = x_hat
            x_prev = x_hat
            dx_prev = dx_hat
            
        return smoothed
