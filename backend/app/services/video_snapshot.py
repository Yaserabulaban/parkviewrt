import json
from pathlib import Path

import cv2

from app.services.occupancy import BASE_DIR, ParkingOccupancyService


VIDEOS_DIR = BASE_DIR / "data" / "videos"
VIDEO_STATUS_CACHE_DIR = BASE_DIR / "data" / "outputs" / "video_status_cache"
SOURCE_VIDEO_EXTENSIONS = (".mov", ".avi", ".mkv", ".mp4")
BROWSER_VIDEO_SUFFIX = "_browser.mp4"


class VideoSnapshotService:
    def __init__(self, occupancy_service: ParkingOccupancyService):
        self.occupancy_service = occupancy_service

    def get_snapshot_status(
        self,
        location_id: str,
        variant: str | None = None,
        frame_index: int = 0,
        include_debug_image: bool = False,
        use_cache: bool = True,
        save_result: bool = True,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        if frame_index < 0:
            raise ValueError("frame_index must be 0 or greater")

        normalized_location_id = location_id.lower()
        normalized_variant = self.occupancy_service._normalize_variant(
            normalized_location_id,
            variant,
        )
        video_path = self._find_video_path(normalized_location_id, normalized_variant)
        cache_path = self._get_status_cache_path(
            normalized_location_id,
            normalized_variant,
            video_path,
            frame_index,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        if use_cache and cache_path.exists() and not include_debug_image:
            return self._read_cached_status(cache_path)

        frame, actual_frame_index = self._read_frame(video_path, frame_index)
        status = self.occupancy_service.get_frame_status(
            normalized_location_id,
            frame,
            variant=normalized_variant,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        status["source"] = {
            "type": "video_snapshot",
            "variant": normalized_variant,
            "video_path": str(video_path),
            "frame_index": actual_frame_index,
            "cached": False,
        }
        if include_debug_image:
            debug_image_path = self.occupancy_service.create_debug_frame_image(
                normalized_location_id,
                frame,
                output_suffix=f"video_frame_{actual_frame_index}",
                variant=normalized_variant,
                overlap_threshold=overlap_threshold,
                box_overlap_threshold=box_overlap_threshold,
                confidence_threshold=confidence_threshold,
                image_size=image_size,
            )
            status["source"]["debug_image_path"] = str(debug_image_path)

        if save_result:
            cache_path = self._get_status_cache_path(
                normalized_location_id,
                normalized_variant,
                video_path,
                actual_frame_index,
                overlap_threshold=overlap_threshold,
                box_overlap_threshold=box_overlap_threshold,
                confidence_threshold=confidence_threshold,
                image_size=image_size,
            )
            self._write_cached_status(cache_path, status)

        return status

    def get_video_path(self, location_id: str, variant: str | None = None) -> Path:
        normalized_location_id = location_id.lower()
        normalized_variant = self.occupancy_service._normalize_variant(
            normalized_location_id,
            variant,
        )
        return self._find_playback_video_path(normalized_location_id, normalized_variant)

    def get_video_metadata(self, location_id: str, variant: str | None = None) -> dict:
        normalized_location_id = location_id.lower()
        normalized_variant = self.occupancy_service._normalize_variant(
            normalized_location_id,
            variant,
        )
        video_path = self._find_playback_video_path(
            normalized_location_id,
            normalized_variant,
        )
        metadata = self._get_video_metadata(video_path)
        fps = metadata["fps"]
        frame_count = metadata["frame_count"]
        duration_seconds = frame_count / fps if fps > 0 and frame_count > 0 else 0

        return {
            "location_id": normalized_location_id,
            "variant": normalized_variant,
            "video_path": str(video_path),
            "file_name": video_path.name,
            "file_size": video_path.stat().st_size,
            "last_modified": video_path.stat().st_mtime,
            "frame_count": frame_count,
            "fps": fps,
            "duration_seconds": duration_seconds,
        }

    def create_debug_snapshot_image(
        self,
        location_id: str,
        variant: str | None = None,
        frame_index: int = 0,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> Path:
        if frame_index < 0:
            raise ValueError("frame_index must be 0 or greater")

        normalized_location_id = location_id.lower()
        normalized_variant = self.occupancy_service._normalize_variant(
            normalized_location_id,
            variant,
        )
        video_path = self._find_video_path(normalized_location_id, normalized_variant)
        frame, actual_frame_index = self._read_frame(video_path, frame_index)
        return self.occupancy_service.create_debug_frame_image(
            normalized_location_id,
            frame,
            output_suffix=f"{normalized_variant}_video_frame_{actual_frame_index}"
            if normalized_variant
            else f"video_frame_{actual_frame_index}",
            variant=normalized_variant,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )

    def get_sampled_status(
        self,
        location_id: str,
        variant: str | None = None,
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
        normalized_variant = self.occupancy_service._normalize_variant(
            normalized_location_id,
            variant,
        )
        video_path = self._find_video_path(normalized_location_id, normalized_variant)
        metadata = self._get_video_metadata(video_path)
        frame_indices = self._build_sample_indices(
            frame_count=metadata["frame_count"],
            sample_count=sample_count,
            start_frame=start_frame,
            frame_step=frame_step,
        )
        samples = self._process_frames(
            location_id=normalized_location_id,
            variant=normalized_variant,
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
                "variant": normalized_variant,
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

    def _find_video_path(self, location_id: str, variant: str | None = None) -> Path:
        location_dir = VIDEOS_DIR / location_id
        candidates = []

        if variant:
            variant_dir = location_dir / variant
            if variant_dir.exists():
                for extension in SOURCE_VIDEO_EXTENSIONS:
                    candidates.extend(sorted(variant_dir.glob(f"*{extension}")))

            if location_dir.exists():
                for extension in SOURCE_VIDEO_EXTENSIONS:
                    candidates.extend(sorted(location_dir.glob(f"*{variant}*{extension}")))

            for extension in SOURCE_VIDEO_EXTENSIONS:
                candidates.extend(sorted(VIDEOS_DIR.glob(f"{location_id}_{variant}*{extension}")))
                archive_dir = VIDEOS_DIR / "archive"
                if archive_dir.exists():
                    candidates.extend(
                        sorted(archive_dir.glob(f"{location_id}_*{variant}*{extension}"))
                    )

            if variant == "day" and location_dir.exists():
                for extension in SOURCE_VIDEO_EXTENSIONS:
                    candidates.extend(sorted(location_dir.glob(f"{location_id}_video{extension}")))
                    candidates.extend(sorted(location_dir.glob(f"video{extension}")))

            candidates = self._exclude_browser_copies(candidates)
            if candidates:
                return candidates[0]

            raise FileNotFoundError(
                f"No {variant} video found for location: {location_id}"
            )

        if location_dir.exists():
            for extension in SOURCE_VIDEO_EXTENSIONS:
                candidates.extend(sorted(location_dir.glob(f"*{extension}")))

        if not candidates:
            for extension in SOURCE_VIDEO_EXTENSIONS:
                candidates.extend(sorted(VIDEOS_DIR.glob(f"{location_id}*{extension}")))

        candidates = self._exclude_browser_copies(candidates)
        if not candidates:
            raise FileNotFoundError(f"No video found for location: {location_id}")

        return candidates[0]

    def _find_playback_video_path(
        self,
        location_id: str,
        variant: str | None = None,
    ) -> Path:
        source_path = self._find_video_path(location_id, variant)
        browser_path = source_path.with_name(f"{source_path.stem}{BROWSER_VIDEO_SUFFIX}")
        if browser_path.exists():
            return browser_path

        return source_path

    def _exclude_browser_copies(self, candidates: list[Path]) -> list[Path]:
        return [
            path
            for path in candidates
            if not path.name.lower().endswith(BROWSER_VIDEO_SUFFIX)
        ]

    def _get_status_cache_path(
        self,
        location_id: str,
        variant: str | None,
        video_path: Path,
        frame_index: int,
        overlap_threshold: float | None,
        box_overlap_threshold: float | None,
        confidence_threshold: float | None,
        image_size: int | None,
    ) -> Path:
        slot_cache_value = self._cache_value(
            overlap_threshold,
            self.occupancy_service.overlap_threshold,
        )
        box_cache_value = self._cache_value(
            box_overlap_threshold,
            self.occupancy_service.box_overlap_threshold,
        )
        confidence_cache_value = self._cache_value(
            confidence_threshold,
            self.occupancy_service.confidence_threshold,
        )
        image_size_cache_value = self._cache_value(
            image_size,
            self.occupancy_service.image_size,
        )
        tuning_key = "_".join(
            [
                f"s{slot_cache_value}",
                f"b{box_cache_value}",
                f"c{confidence_cache_value}",
                f"i{image_size_cache_value}",
            ]
        )
        slot_key = self._get_slot_cache_key(location_id, variant)
        video_key = self._get_video_cache_key(video_path)
        return (
            VIDEO_STATUS_CACHE_DIR
            / location_id
            / (variant or "default")
            / video_key
            / slot_key
            / tuning_key
            / f"frame_{frame_index}.json"
        )

    def _get_video_cache_key(self, video_path: Path) -> str:
        stat = video_path.stat()
        extension = video_path.suffix.lower().lstrip(".") or "video"
        return f"{video_path.stem}_{extension}_{stat.st_mtime_ns}_{stat.st_size}"

    def _get_slot_cache_key(self, location_id: str, variant: str | None) -> str:
        slot_path = BASE_DIR / "data" / "slots" / f"{location_id}_{variant}_slots.json"
        if not slot_path.exists():
            return "slots_missing"

        stat = slot_path.stat()
        return f"slots_{stat.st_mtime_ns}_{stat.st_size}"

    def _cache_value(self, value, default_value) -> str:
        resolved_value = default_value if value is None else value
        return str(resolved_value).replace(".", "p")

    def _read_cached_status(self, cache_path: Path) -> dict:
        with cache_path.open("r", encoding="utf-8") as cache_file:
            status = json.load(cache_file)
        status.setdefault("source", {})
        status["source"]["cached"] = True
        status["source"]["cache_path"] = str(cache_path)
        return status

    def _write_cached_status(self, cache_path: Path, status: dict) -> None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cached_status = json.loads(json.dumps(status))
        cached_status.setdefault("source", {})
        cached_status["source"]["cache_path"] = str(cache_path)
        with cache_path.open("w", encoding="utf-8") as cache_file:
            json.dump(cached_status, cache_file, indent=2)

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
        variant: str | None,
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
                    variant=variant,
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
