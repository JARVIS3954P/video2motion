import cv2
import os

class VideoLoader:
    def __init__(self, video_path, start_time=None, end_time=None):
        """
        Initialize the VideoLoader.
        
        Args:
            video_path (str): Path to the input video file.
            start_time (float, optional): Start time in seconds.
            end_time (float, optional): End time in seconds.
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
        
        # Calculate frame count based on start and end time if provided
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / self.fps if self.fps > 0 else 0
        
        self.start_time = start_time if start_time is not None else 0.0
        self.end_time = end_time if end_time is not None else duration
        
        if self.start_time > 0:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, self.start_time * 1000)
            
        expected_frames = int((self.end_time - self.start_time) * self.fps)
        self.frame_count = min(expected_frames, total_frames)
        
        print(f"Video loaded: {video_path}")
        print(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Trimmed Frames: {self.frame_count}")

    def __iter__(self):
        return self

    def __next__(self):
        """
        Yields the next frame from the video.
        
        Returns:
            frame (np.array): BGR image frames.
        """
        current_msec = self.cap.get(cv2.CAP_PROP_POS_MSEC)
        if current_msec > self.end_time * 1000:
            self.cap.release()
            raise StopIteration
            
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            raise StopIteration
        return frame

    def release(self):
        """Release the video capture object."""
        if self.cap.isOpened():
            self.cap.release()
