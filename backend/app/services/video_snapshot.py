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
        include_debug_image: bool = False,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        if frame_index < 0:
            raise ValueError("frame_index must be 0 or greater")

        normalized_location_id = location_id.lower()
        video_path = self._find_video_path(normalized_location_id)
        frame, actual_frame_index = self._read_frame(video_path, frame_index)
        status = self.occupancy_service.get_frame_status(
            normalized_location_id,
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
        if include_debug_image:
            debug_image_path = self.occupancy_service.create_debug_frame_image(
                normalized_location_id,
                frame,
                output_suffix=f"video_frame_{actual_frame_index}",
                overlap_threshold=overlap_threshold,
                box_overlap_threshold=box_overlap_threshold,
                confidence_threshold=confidence_threshold,
                image_size=image_size,
            )
            status["source"]["debug_image_path"] = str(debug_image_path)

        return status

    def get_video_path(self, location_id: str) -> Path:
        return self._find_video_path(location_id.lower())

    def get_sampled_status(
        self,
        location_id: str,
        sample_count: int = 5,
        start_frame: int = 0,
        frame_step: int = 30,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        if sample_count < 1 or sample_count > 20:
            raise ValueError("sample_count must be between 1 and 20")
        if start_frame < 0:
            raise ValueError("start_frame must be 0 or greater")
        if frame_step < 1:
            raise ValueError("frame_step must be 1 or greater")

        normalized_location_id = location_id.lower()
        video_path = self._find_video_path(normalized_location_id)
        metadata = self._get_video_metadata(video_path)
        frame_indices = self._build_sample_indices(
            frame_count=metadata["frame_count"],
            sample_count=sample_count,
            start_frame=start_frame,
            frame_step=frame_step,
        )
        samples = self._process_frames(
            location_id=normalized_location_id,
            video_path=video_path,
            frame_indices=frame_indices,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )

        return {
            "location_id": normalized_location_id,
            "source": {
                "type": "video_samples",
                "video_path": str(video_path),
                "frame_count": metadata["frame_count"],
                "fps": metadata["fps"],
                "sample_count": len(samples),
                "start_frame": start_frame,
                "frame_step": frame_step,
                "frame_indices": frame_indices,
            },
            "summary": self._summarize_samples(samples),
            "samples": samples,
        }

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

    def _get_video_metadata(self, video_path: Path) -> dict:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Unable to open video: {video_path}")

        try:
            return {
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": float(cap.get(cv2.CAP_PROP_FPS) or 0),
            }
        finally:
            cap.release()

    def _build_sample_indices(
        self,
        frame_count: int,
        sample_count: int,
        start_frame: int,
        frame_step: int,
    ) -> list[int]:
        if frame_count <= 0:
            return [start_frame + index * frame_step for index in range(sample_count)]

        if start_frame >= frame_count:
            raise ValueError(
                f"start_frame must be less than video frame count ({frame_count})"
            )

        frame_indices = []
        for index in range(sample_count):
            frame_index = start_frame + index * frame_step
            if frame_index >= frame_count:
                break
            frame_indices.append(frame_index)

        return frame_indices

    def _process_frames(
        self,
        location_id: str,
        video_path: Path,
        frame_indices: list[int],
        overlap_threshold: float | None,
        box_overlap_threshold: float | None,
        confidence_threshold: float | None,
        image_size: int | None,
    ) -> list[dict]:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Unable to open video: {video_path}")

        samples = []
        try:
            for frame_index in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                success, frame = cap.read()
                if not success or frame is None:
                    raise ValueError(
                        f"Unable to read frame {frame_index} from video: {video_path}"
                    )

                status = self.occupancy_service.get_frame_status(
                    location_id,
                    frame,
                    overlap_threshold=overlap_threshold,
                    box_overlap_threshold=box_overlap_threshold,
                    confidence_threshold=confidence_threshold,
                    image_size=image_size,
                )
                samples.append(
                    {
                        "frame_index": frame_index,
                        "total_slots": status["total_slots"],
                        "occupied_count": status["occupied_count"],
                        "available_count": status["available_count"],
                        "slots": status["slots"],
                    }
                )
        finally:
            cap.release()

        if not samples:
            raise ValueError("No frames were sampled from video")

        return samples

    def _summarize_samples(self, samples: list[dict]) -> dict:
        sample_count = len(samples)
        latest_sample = samples[-1]
        slot_ids = [slot["slot_id"] for slot in latest_sample["slots"]]
        slot_summary = []

        for slot_id in slot_ids:
            occupied_frames = sum(
                1
                for sample in samples
                for slot in sample["slots"]
                if slot["slot_id"] == slot_id and slot["occupied"]
            )
            occupancy_ratio = occupied_frames / sample_count
            slot_summary.append(
                {
                    "slot_id": slot_id,
                    "occupied_frames": occupied_frames,
                    "sample_count": sample_count,
                    "occupancy_ratio": occupancy_ratio,
                    "occupied": occupancy_ratio >= 0.5,
                }
            )

        occupied_count = sum(1 for slot in slot_summary if slot["occupied"])
        total_slots = len(slot_summary)

        return {
            "total_slots": total_slots,
            "occupied_count": occupied_count,
            "available_count": total_slots - occupied_count,
            "sample_count": sample_count,
            "latest_frame_index": latest_sample["frame_index"],
            "slots": slot_summary,
        }
