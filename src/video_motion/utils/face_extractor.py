import cv2
import numpy as np
import base64
import os

def extract_face_b64(image_bytes: bytes) -> str | None:
    """
    Takes an image (bytes) and uses OpenCV Haar Cascades to crop the face.
    Returns a base64 encoded PNG string of the cropped face, or None if no face found.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Use OpenCV's built-in Haar cascade for frontal face
    cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return None
        
    # Get the largest face
    faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
    x, y, w, h_box = faces[0]
    
    img_h, img_w, _ = img.shape
    
    # Add padding around the face
    pad_x = int(w * 0.2)
    pad_y = int(h_box * 0.3)
    
    x_start = max(0, x - pad_x)
    y_start = max(0, y - pad_y)
    x_end = min(img_w, x + w + pad_x)
    y_end = min(img_h, y + h_box + pad_y)
    
    face_crop = img[y_start:y_end, x_start:x_end]
    
    if face_crop.size == 0:
        return None
        
    # Resize to standard texture size (e.g. 256x256)
    face_resized = cv2.resize(face_crop, (256, 256))
    
    # Create an alpha channel (oval mask)
    mask = np.zeros((256, 256), dtype=np.uint8)
    cv2.ellipse(mask, (128, 128), (100, 120), 0, 0, 360, 255, -1)
    
    # Blur the mask edges
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    b, g, r = cv2.split(face_resized)
    rgba = [b, g, r, mask]
    face_rgba = cv2.merge(rgba, 4)
    
    _, buffer = cv2.imencode('.png', face_rgba)
    return base64.b64encode(buffer).decode('utf-8')
