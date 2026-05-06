from functools import lru_cache
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from app.settings import get_settings

DEFAULT_MODEL_PATH = get_settings().detection.model_path


class YoloDetector:
    def __init__(self, model_path: str | Path = DEFAULT_MODEL_PATH):
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model = YOLO(str(model_path))
        self.allowed_classes = {"car", "truck"}

    def detect_cars(
        self,
        image: str | Path | Any,
        confidence_threshold: float = 0.25,
        image_size: int = 640,
    ) -> list[dict]:
        results = self.model(
            str(image) if isinstance(image, Path) else image,
            conf=confidence_threshold,
            imgsz=image_size,
            verbose=False,
        )
        detections = []

        for result in results:
            names = result.names
            for detected_box in result.boxes:
                cls_id = int(detected_box.cls[0].item())
                cls_name = names[cls_id]

                if cls_name not in self.allowed_classes:
                    continue

                x1, y1, x2, y2 = detected_box.xyxy[0].tolist()

                detections.append(
                    {
                        "class_name": cls_name,
                        "confidence": float(detected_box.conf[0].item()),
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    }
                )

        return detections

    def detect_vehicles(
        self,
        frame: Any,
        confidence_threshold: float = 0.25,
        image_size: int = 640,
    ) -> list[dict]:
        return self.detect_cars(
            frame,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )


@lru_cache(maxsize=1)
def get_yolo_detector(model_path: str | Path = DEFAULT_MODEL_PATH) -> YoloDetector:
    return YoloDetector(model_path=model_path)
