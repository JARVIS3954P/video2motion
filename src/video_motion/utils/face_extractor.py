import cv2
import numpy as np
import base64

def extract_face_b64(image_bytes: bytes) -> str:
    """
    Extracts the largest face from an image (provided as bytes),
    crops it with a margin, resizes it to 256x256, and returns it
    as a base64 encoded PNG string.
    Returns None if no face is detected.
    """
    # Decode image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return None

    # Load Haar cascade for face detection
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.1, 
        minNeighbors=5, 
        minSize=(30, 30)
    )
    
    if len(faces) == 0:
        return None
        
    # Pick the largest face by area
    faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
    x, y, w, h = faces[0]
    
    # Crop the face with a slight margin
    margin_w = int(w * 0.1)
    margin_h = int(h * 0.2)
    
    y1 = max(0, y - margin_h)
    y2 = min(img.shape[0], y + h + margin_h)
    x1 = max(0, x - margin_w)
    x2 = min(img.shape[1], x + w + margin_w)
    
    face_crop = img[y1:y2, x1:x2]
    
    # Resize to a reasonable size for a 3D avatar texture
    face_crop = cv2.resize(face_crop, (256, 256))
    
    # Encode as PNG
    success, encoded_img = cv2.imencode('.png', face_crop)
    if not success:
        return None
        
    b64_str = base64.b64encode(encoded_img).decode('utf-8')
    return b64_str
