import cv2


class VideoReader:
    def __init__(self, video_path: str):
        self.video_path = video_path

    def open(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video: {self.video_path}")
        return cap