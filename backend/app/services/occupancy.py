import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Point, Polygon, box

from app.services.yolo_detector import get_yolo_detector


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
IMAGES_DIR = BASE_DIR / "data" / "images"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
VALID_LOCATION_IDS = {"fci", "faie"}


class ParkingOccupancyService:
    def __init__(
        self,
        overlap_threshold: float = 0.30,
        box_overlap_threshold: float = 0.20,
        confidence_threshold: float = 0.20,
        image_size: int = 1600,
    ):
        self.overlap_threshold = overlap_threshold
        self.box_overlap_threshold = box_overlap_threshold
        self.confidence_threshold = confidence_threshold
        self.image_size = image_size
        self.detector = get_yolo_detector()

    def get_status(
        self,
        location_id: str,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        analysis = self._analyze_location(
            location_id,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        slots = [
            {"slot_id": slot["slot_id"], "occupied": slot["occupied"]}
            for slot in analysis["slots"]
        ]

        occupied_count = sum(1 for slot in slots if slot["occupied"])
        total_slots = len(slots)

        return {
            "location_id": analysis["location_id"],
            "total_slots": total_slots,
            "occupied_count": occupied_count,
            "available_count": total_slots - occupied_count,
            "slots": slots,
        }

    def create_debug_image(
        self,
        location_id: str,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> Path:
        analysis = self._analyze_location(
            location_id,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        image = cv2.imread(str(analysis["image_path"]))
        if image is None:
            raise FileNotFoundError(f"Unable to read parking image: {analysis['image_path']}")

        slot_lookup = {slot["slot_id"]: slot for slot in analysis["slots"]}
        self._draw_slots(image, analysis["slot_data"]["slots"], slot_lookup)
        self._draw_detections(image, analysis["detections"])
        self._draw_summary(image, analysis)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUTS_DIR / f"{analysis['location_id']}_debug.jpg"
        cv2.imwrite(str(output_path), image)
        return output_path

    def _analyze_location(
        self,
        location_id: str,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        normalized_location_id = location_id.lower()
        resolved_overlap_threshold = self._resolve_threshold(
            overlap_threshold,
            self.overlap_threshold,
            "overlap threshold",
        )
        resolved_box_overlap_threshold = self._resolve_threshold(
            box_overlap_threshold,
            self.box_overlap_threshold,
            "box overlap threshold",
        )
        resolved_confidence_threshold = self._resolve_threshold(
            confidence_threshold,
            self.confidence_threshold,
            "confidence threshold",
        )
        resolved_image_size = self._resolve_image_size(image_size)
        slot_data = self._load_slots(normalized_location_id)
        image_path = self._get_image_path(normalized_location_id)
        detections = self.detector.detect_cars(
            image_path,
            confidence_threshold=resolved_confidence_threshold,
            image_size=resolved_image_size,
        )
        slots = self._calculate_slot_occupancy(
            slot_data["slots"],
            detections,
            overlap_threshold=resolved_overlap_threshold,
            box_overlap_threshold=resolved_box_overlap_threshold,
        )

        return {
            "location_id": slot_data.get("location_id", normalized_location_id),
            "slot_data": slot_data,
            "image_path": image_path,
            "detections": detections,
            "slots": slots,
            "overlap_threshold": resolved_overlap_threshold,
            "box_overlap_threshold": resolved_box_overlap_threshold,
            "confidence_threshold": resolved_confidence_threshold,
            "image_size": resolved_image_size,
        }

    def _resolve_threshold(
        self,
        value: float | None,
        default: float,
        label: str,
    ) -> float:
        resolved_value = default if value is None else value
        if resolved_value < 0 or resolved_value > 1:
            raise ValueError(f"{label} must be between 0 and 1")
        return resolved_value

    def _resolve_image_size(self, image_size: int | None) -> int:
        resolved_image_size = self.image_size if image_size is None else image_size
        if resolved_image_size < 320 or resolved_image_size > 2048:
            raise ValueError("image size must be between 320 and 2048")
        return resolved_image_size

    def _load_slots(self, location_id: str) -> dict:
        if location_id not in VALID_LOCATION_IDS:
            raise ValueError(f"Unknown location: {location_id}")

        slot_path = SLOTS_DIR / f"{location_id}_slots.json"
        if not slot_path.exists():
            raise FileNotFoundError(f"Slot file not found: {slot_path}")

        with slot_path.open("r", encoding="utf-8") as slot_file:
            return json.load(slot_file)

    def _get_image_path(self, location_id: str) -> Path:
        for extension in (".jpg", ".jpeg", ".png"):
            image_path = IMAGES_DIR / f"{location_id}{extension}"
            if image_path.exists():
                return image_path

        raise FileNotFoundError(f"Parking image not found for location: {location_id}")

    def _calculate_slot_occupancy(
        self,
        slots: list[dict],
        detections: list[dict],
        overlap_threshold: float,
        box_overlap_threshold: float,
    ) -> list[dict]:
        occupancy_results = []

        for slot in slots:
            slot_polygon = Polygon(slot["points"])
            slot_area = slot_polygon.area
            best_overlap_ratio = 0
            best_box_overlap_ratio = 0
            detection_center_in_slot = False
            slot_centroid_in_detection = False
            occupied = False
            occupied_reason = "none"

            if slot_area > 0:
                for detection in detections:
                    detection_box = box(*detection["bbox"])
                    detection_area = detection_box.area
                    detection_center = Point(detection_box.centroid.x, detection_box.centroid.y)
                    intersection_area = slot_polygon.intersection(detection_box).area
                    overlap_ratio = intersection_area / slot_area
                    box_overlap_ratio = (
                        intersection_area / detection_area if detection_area > 0 else 0
                    )
                    best_overlap_ratio = max(best_overlap_ratio, overlap_ratio)
                    best_box_overlap_ratio = max(best_box_overlap_ratio, box_overlap_ratio)
                    detection_center_in_slot = (
                        detection_center_in_slot or slot_polygon.contains(detection_center)
                    )
                    slot_centroid_in_detection = (
                        slot_centroid_in_detection
                        or detection_box.contains(slot_polygon.centroid)
                    )

                    if overlap_ratio >= overlap_threshold:
                        occupied = True
                        occupied_reason = "slot-overlap"
                    elif box_overlap_ratio >= box_overlap_threshold:
                        occupied = True
                        occupied_reason = "box-overlap"
                    elif slot_polygon.contains(detection_center):
                        occupied = True
                        occupied_reason = "detection-center"
                    elif detection_box.contains(slot_polygon.centroid):
                        occupied = True
                        occupied_reason = "slot-centroid"

            occupancy_results.append(
                {
                    "slot_id": slot["slot_id"],
                    "occupied": occupied,
                    "overlap_ratio": best_overlap_ratio,
                    "box_overlap_ratio": best_box_overlap_ratio,
                    "detection_center_in_slot": detection_center_in_slot,
                    "slot_centroid_in_detection": slot_centroid_in_detection,
                    "occupied_reason": occupied_reason,
                }
            )

        return occupancy_results

    def _draw_slots(self, image, slots: list[dict], slot_lookup: dict) -> None:
        overlay = image.copy()

        for slot in slots:
            slot_status = slot_lookup[slot["slot_id"]]
            points = np.array(slot["points"], dtype=np.int32)
            color = (0, 0, 255) if slot_status["occupied"] else (0, 180, 0)

            cv2.fillPoly(overlay, [points], color)

        cv2.addWeighted(overlay, 0.25, image, 0.75, 0, image)

        for slot in slots:
            slot_status = slot_lookup[slot["slot_id"]]
            points = np.array(slot["points"], dtype=np.int32)
            color = (0, 0, 255) if slot_status["occupied"] else (0, 180, 0)
            reason = slot_status["occupied_reason"]
            label = f"{slot['slot_id']} S{slot_status['overlap_ratio']:.0%}"
            if slot_status["occupied"] and reason != "slot-overlap":
                label = f"{label} {self._short_reason(reason)}"

            cv2.polylines(image, [points], isClosed=True, color=color, thickness=3)

            label_x, label_y = points.mean(axis=0).astype(int)
            cv2.putText(
                image,
                label,
                (label_x - 25, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

    def _draw_detections(self, image, detections: list[dict]) -> None:
        for detection in detections:
            x1, y1, x2, y2 = [int(value) for value in detection["bbox"]]
            confidence = detection["confidence"]

            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 180, 0), 3)
            cv2.putText(
                image,
                f"car {confidence:.2f}",
                (x1, max(y1 - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 180, 0),
                2,
            )

    def _draw_summary(self, image, analysis: dict) -> None:
        total_slots = len(analysis["slots"])
        occupied_count = sum(1 for slot in analysis["slots"] if slot["occupied"])
        available_count = total_slots - occupied_count
        detection_count = len(analysis["detections"])
        summary = (
            f"{analysis['location_id'].upper()} | "
            f"slots: {total_slots} | occupied: {occupied_count} | "
            f"available: {available_count} | cars detected: {detection_count} | "
            f"S>={analysis['overlap_threshold']:.2f} "
            f"B>={analysis['box_overlap_threshold']:.2f} "
            f"C>={analysis['confidence_threshold']:.2f} "
            f"imgsz={analysis['image_size']}"
        )

        cv2.rectangle(image, (20, 20), (1500, 72), (0, 0, 0), -1)
        cv2.putText(
            image,
            summary,
            (35, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (255, 255, 255),
            2,
        )

    def _short_reason(self, reason: str) -> str:
        return {
            "box-overlap": "B",
            "detection-center": "C",
            "slot-centroid": "SC",
        }.get(reason, "")
