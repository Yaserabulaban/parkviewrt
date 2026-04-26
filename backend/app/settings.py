import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DetectionSettings:
    model_path: Path
    confidence_threshold: float
    image_size: int
    slot_overlap_threshold: float
    box_overlap_threshold: float

    def as_dict(self) -> dict:
        return {
            "model_path": str(self.model_path),
            "confidence_threshold": self.confidence_threshold,
            "image_size": self.image_size,
            "slot_overlap_threshold": self.slot_overlap_threshold,
            "box_overlap_threshold": self.box_overlap_threshold,
        }


@dataclass(frozen=True)
class AppSettings:
    detection: DetectionSettings


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _env_path(name: str, default: Path) -> Path:
    raw_value = os.getenv(name)
    if not raw_value:
        return default

    path = Path(raw_value)
    if path.is_absolute():
        return path

    for base_path in (Path.cwd(), BASE_DIR.parent, BASE_DIR.parent.parent):
        candidate = base_path / path
        if candidate.exists() or candidate.parent.exists():
            return candidate

    return BASE_DIR.parent.parent / path


def _validate_unit_interval(value: float, label: str) -> float:
    if value < 0 or value > 1:
        raise ValueError(f"{label} must be between 0 and 1")
    return value


def _validate_image_size(value: int) -> int:
    if value < 320 or value > 2048:
        raise ValueError("PARKVIEWRT_IMAGE_SIZE must be between 320 and 2048")
    return value


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    detection = DetectionSettings(
        model_path=_env_path(
            "PARKVIEWRT_MODEL_PATH",
            BASE_DIR / "models" / "yolo11n.pt",
        ),
        confidence_threshold=_validate_unit_interval(
            _env_float("PARKVIEWRT_CONFIDENCE", 0.20),
            "PARKVIEWRT_CONFIDENCE",
        ),
        image_size=_validate_image_size(_env_int("PARKVIEWRT_IMAGE_SIZE", 1600)),
        slot_overlap_threshold=_validate_unit_interval(
            _env_float("PARKVIEWRT_SLOT_THRESHOLD", 0.30),
            "PARKVIEWRT_SLOT_THRESHOLD",
        ),
        box_overlap_threshold=_validate_unit_interval(
            _env_float("PARKVIEWRT_BOX_THRESHOLD", 0.20),
            "PARKVIEWRT_BOX_THRESHOLD",
        ),
    )
    return AppSettings(detection=detection)
