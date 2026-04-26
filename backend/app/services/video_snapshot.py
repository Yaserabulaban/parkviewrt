from pathlib import Path

import cv2

from app.services.occupancy import BASE_DIR, ParkingOccupancyService


VIDEOS_DIR = BASE_DIR / "data" / "videos"
SUPPORTED_VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")


class VideoSnapshotService:
    def __init__(self, occupancy_service: ParkingOccupancyService):
        self.occupancy_service = occupancy_service

    def get_snapshot_status(
        self,
        location_id: str,
        frame_index: int = 0,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        if frame_index < 0:
            raise ValueError("frame_index must be 0 or greater")

        video_path = self._find_video_path(location_id.lower())
        frame, actual_frame_index = self._read_frame(video_path, frame_index)
        status = self.occupancy_service.get_frame_status(
            location_id,
            frame,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        status["source"] = {
            "type": "video_snapshot",
            "video_path": str(video_path),
            "frame_index": actual_frame_index,
        }
        return status

    def _find_video_path(self, location_id: str) -> Path:
        location_dir = VIDEOS_DIR / location_id
        candidates = []

        if location_dir.exists():
            for extension in SUPPORTED_VIDEO_EXTENSIONS:
                candidates.extend(sorted(location_dir.glob(f"*{extension}")))

        if not candidates:
            for extension in SUPPORTED_VIDEO_EXTENSIONS:
                candidates.extend(sorted(VIDEOS_DIR.glob(f"{location_id}*{extension}")))

        if not candidates:
            raise FileNotFoundError(f"No video found for location: {location_id}")

        return candidates[0]

    def _read_frame(self, video_path: Path, frame_index: int):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Unable to open video: {video_path}")

        try:
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            actual_frame_index = frame_index
            if frame_count > 0:
                actual_frame_index = min(frame_index, frame_count - 1)

            cap.set(cv2.CAP_PROP_POS_FRAMES, actual_frame_index)
            success, frame = cap.read()
            if not success or frame is None:
                raise ValueError(f"Unable to read frame from video: {video_path}")

            return frame, actual_frame_index
        finally:
            cap.release()
