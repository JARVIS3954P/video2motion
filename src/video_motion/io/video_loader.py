import cv2
import os

class VideoLoader:
    def __init__(self, video_path):
        """
        Initialize the VideoLoader.
        
        Args:
            video_path (str): Path to the input video file.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video loaded: {video_path}")
        print(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Frames: {self.frame_count}")

    def __iter__(self):
        return self

    def __next__(self):
        """
        Yields the next frame from the video.
        
        Returns:
            frame (np.array): BGR image frames.
        """
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise StopIteration
        return frame

    def release(self):
        """Release the video capture object."""
        if self.cap.isOpened():
            self.cap.release()
