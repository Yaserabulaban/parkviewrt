import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Point, Polygon, box

from app.settings import AppSettings, get_settings
from app.services.yolo_detector import get_yolo_detector


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
IMAGES_DIR = BASE_DIR / "data" / "images"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
VALID_LOCATION_IDS = {"fci", "faie"}
VALID_VIDEO_VARIANTS = {"day", "night"}
DEFAULT_VIDEO_VARIANTS = {
    "fci": "day",
    "faie": "day",
}
KNOWN_OCCLUDED_SLOTS = {
    ("fci", "day"): {"A7", "A10", "A50", "A60", "A61", "A62", "A64"},
}


class ParkingOccupancyService:
    def __init__(
        self,
        settings: AppSettings | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ):
        self.settings = settings or get_settings()
        detection_settings = self.settings.detection
        self.overlap_threshold = (
            detection_settings.slot_overlap_threshold
            if overlap_threshold is None
            else overlap_threshold
        )
        self.box_overlap_threshold = (
            detection_settings.box_overlap_threshold
            if box_overlap_threshold is None
            else box_overlap_threshold
        )
        self.confidence_threshold = (
            detection_settings.confidence_threshold
            if confidence_threshold is None
            else confidence_threshold
        )
        self.image_size = detection_settings.image_size if image_size is None else image_size
        self.detector = get_yolo_detector(detection_settings.model_path)

    def get_status(
        self,
        location_id: str,
        variant: str | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        analysis = self._analyze_location(
            location_id,
            variant=variant,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        return self._build_status_response(analysis)

    def get_frame_status(
        self,
        location_id: str,
        frame,
        variant: str | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        analysis = self._analyze_location(
            location_id,
            image_source=frame,
            variant=variant,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        return self._build_status_response(analysis)

    def _build_status_response(self, analysis: dict) -> dict:
        slots = [
            {
                "slot_id": slot["slot_id"],
                "occupied": slot["occupied"],
                "status": slot["status"],
            }
            for slot in analysis["slots"]
        ]

        occupied_count = sum(1 for slot in slots if slot["status"] == "occupied")
        occluded_count = sum(1 for slot in slots if slot["status"] == "occluded")
        total_slots = len(slots)

        return {
            "location_id": analysis["location_id"],
            "total_slots": total_slots,
            "occupied_count": occupied_count,
            "available_count": total_slots - occupied_count - occluded_count,
            "occluded_count": occluded_count,
            "slots": slots,
        }

    def create_debug_image(
        self,
        location_id: str,
        variant: str | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> Path:
        analysis = self._analyze_location(
            location_id,
            variant=variant,
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
        output_name = f"{analysis['location_id']}_debug.jpg"
        if analysis["variant"]:
            output_name = f"{analysis['location_id']}_{analysis['variant']}_debug.jpg"
        output_path = OUTPUTS_DIR / output_name
        cv2.imwrite(str(output_path), image)
        return output_path

    def create_debug_frame_image(
        self,
        location_id: str,
        frame,
        output_suffix: str,
        variant: str | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> Path:
        analysis = self._analyze_location(
            location_id,
            image_source=frame,
            variant=variant,
            overlap_threshold=overlap_threshold,
            box_overlap_threshold=box_overlap_threshold,
            confidence_threshold=confidence_threshold,
            image_size=image_size,
        )
        image = frame.copy()

        slot_lookup = {slot["slot_id"]: slot for slot in analysis["slots"]}
        self._draw_slots(image, analysis["slot_data"]["slots"], slot_lookup)
        self._draw_detections(image, analysis["detections"])
        self._draw_summary(image, analysis)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUTS_DIR / f"{analysis['location_id']}_{output_suffix}_debug.jpg"
        cv2.imwrite(str(output_path), image)
        return output_path

    def _analyze_location(
        self,
        location_id: str,
        image_source=None,
        variant: str | None = None,
        overlap_threshold: float | None = None,
        box_overlap_threshold: float | None = None,
        confidence_threshold: float | None = None,
        image_size: int | None = None,
    ) -> dict:
        normalized_location_id = location_id.lower()
        normalized_variant = self._normalize_variant(normalized_location_id, variant)
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
        slot_data = self._load_slots(normalized_location_id, normalized_variant)
        image_path = (
            self._get_image_path(normalized_location_id, normalized_variant)
            if image_source is None
            else None
        )
        resolved_image_source = image_path if image_source is None else image_source
        detections = self.detector.detect_vehicles(
            resolved_image_source,
            confidence_threshold=resolved_confidence_threshold,
            image_size=resolved_image_size,
        )
        slots = self._calculate_slot_occupancy(
            slot_data["slots"],
            detections,
            overlap_threshold=resolved_overlap_threshold,
            box_overlap_threshold=resolved_box_overlap_threshold,
        )
        self._apply_known_occlusions(
            normalized_location_id,
            normalized_variant,
            slots,
        )

        return {
            "location_id": slot_data.get("location_id", normalized_location_id),
            "variant": normalized_variant,
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

    def _normalize_variant(self, location_id: str, variant: str | None) -> str | None:
        if location_id not in VALID_LOCATION_IDS:
            raise ValueError(f"Unknown location: {location_id}")

        normalized_variant = (
            DEFAULT_VIDEO_VARIANTS[location_id]
            if variant is None
            else variant.lower()
        )
        if normalized_variant not in VALID_VIDEO_VARIANTS:
            raise ValueError("variant must be either day or night")

        return normalized_variant

    def _load_slots(self, location_id: str, variant: str | None = None) -> dict:
        normalized_variant = self._normalize_variant(location_id, variant)
        slot_path = SLOTS_DIR / f"{location_id}_{normalized_variant}_slots.json"
        if not slot_path.exists():
            raise FileNotFoundError(
                f"Slot file not found for location: {location_id}, variant: {normalized_variant}"
            )

        with slot_path.open("r", encoding="utf-8") as slot_file:
            return json.load(slot_file)

    def _get_image_path(self, location_id: str, variant: str | None = None) -> Path:
        normalized_variant = self._normalize_variant(location_id, variant)
        image_names = [f"{location_id}_{normalized_variant}", location_id]

        for image_name in image_names:
            for extension in (".jpg", ".jpeg", ".png"):
                image_path = IMAGES_DIR / f"{image_name}{extension}"
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
        slot_geometries = [
            {
                "slot": slot,
                "polygon": Polygon(slot["points"]),
            }
            for slot in slots
        ]
        occupancy_results = [
            {
                "slot_id": slot["slot_id"],
                "occupied": False,
                "status": "available",
                "overlap_ratio": 0,
                "box_overlap_ratio": 0,
                "detection_center_in_slot": False,
                "slot_centroid_in_detection": False,
                "occupied_reason": "none",
            }
            for slot in slots
        ]

        for detection in detections:
            detection_box = box(*detection["bbox"])
            detection_area = detection_box.area
            if detection_area <= 0:
                continue

            detection_center = Point(detection_box.centroid.x, detection_box.centroid.y)
            best_candidate = None

            for index, slot_geometry in enumerate(slot_geometries):
                slot_polygon = slot_geometry["polygon"]
                slot_area = slot_polygon.area
                if slot_area <= 0:
                    continue

                intersection_area = slot_polygon.intersection(detection_box).area
                overlap_ratio = intersection_area / slot_area
                box_overlap_ratio = intersection_area / detection_area
                detection_center_in_slot = slot_polygon.contains(detection_center)
                slot_centroid_in_detection = detection_box.contains(slot_polygon.centroid)
                slot_result = occupancy_results[index]
                slot_result["overlap_ratio"] = max(
                    slot_result["overlap_ratio"],
                    overlap_ratio,
                )
                slot_result["box_overlap_ratio"] = max(
                    slot_result["box_overlap_ratio"],
                    box_overlap_ratio,
                )
                slot_result["detection_center_in_slot"] = (
                    slot_result["detection_center_in_slot"] or detection_center_in_slot
                )
                slot_result["slot_centroid_in_detection"] = (
                    slot_result["slot_centroid_in_detection"] or slot_centroid_in_detection
                )

                reason = None
                score = 0
                if detection_center_in_slot:
                    reason = "detection-center"
                    score = 3 + overlap_ratio
                elif overlap_ratio >= overlap_threshold:
                    reason = "slot-overlap"
                    score = 2 + overlap_ratio
                elif box_overlap_ratio >= box_overlap_threshold:
                    reason = "box-overlap"
                    score = 1 + box_overlap_ratio
                elif slot_centroid_in_detection:
                    reason = "slot-centroid"
                    score = 0.5 + overlap_ratio

                if reason and (
                    best_candidate is None or score > best_candidate["score"]
                ):
                    best_candidate = {
                        "index": index,
                        "score": score,
                        "reason": reason,
                    }

            if best_candidate is not None:
                occupied_slot = occupancy_results[best_candidate["index"]]
                occupied_slot["occupied"] = True
                occupied_slot["status"] = "occupied"
                occupied_slot["occupied_reason"] = best_candidate["reason"]

        return occupancy_results

    def _apply_known_occlusions(
        self,
        location_id: str,
        variant: str | None,
        slots: list[dict],
    ) -> None:
        occluded_slot_ids = KNOWN_OCCLUDED_SLOTS.get((location_id, variant), set())
        if not occluded_slot_ids:
            return

        for slot in slots:
            if slot["slot_id"] in occluded_slot_ids and not slot["occupied"]:
                slot["occupied"] = False
                slot["status"] = "occluded"
                slot["occupied_reason"] = "known-occlusion"

    def _draw_slots(self, image, slots: list[dict], slot_lookup: dict) -> None:
        overlay = image.copy()

        for slot in slots:
            slot_status = slot_lookup[slot["slot_id"]]
            points = np.array(slot["points"], dtype=np.int32)
            color = self._status_color(slot_status["status"])

            cv2.fillPoly(overlay, [points], color)

        cv2.addWeighted(overlay, 0.25, image, 0.75, 0, image)

        for slot in slots:
            slot_status = slot_lookup[slot["slot_id"]]
            points = np.array(slot["points"], dtype=np.int32)
            color = self._status_color(slot_status["status"])
            reason = slot_status["occupied_reason"]
            label = f"{slot['slot_id']} S{slot_status['overlap_ratio']:.0%}"
            if slot_status["status"] == "occluded":
                label = f"{slot['slot_id']} OCC"
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
            class_name = detection.get("class_name", "vehicle")

            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 180, 0), 3)
            cv2.putText(
                image,
                f"{class_name} {confidence:.2f}",
                (x1, max(y1 - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 180, 0),
                2,
            )

    def _draw_summary(self, image, analysis: dict) -> None:
        total_slots = len(analysis["slots"])
        occupied_count = sum(1 for slot in analysis["slots"] if slot["occupied"])
        occluded_count = sum(1 for slot in analysis["slots"] if slot["status"] == "occluded")
        available_count = total_slots - occupied_count - occluded_count
        detection_count = len(analysis["detections"])
        summary = (
            f"{analysis['location_id'].upper()} | "
            f"slots: {total_slots} | occupied: {occupied_count} | "
            f"available: {available_count} | occluded: {occluded_count} | "
            f"vehicles detected: {detection_count} | "
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

    def _status_color(self, status: str) -> tuple[int, int, int]:
        if status == "occupied":
            return (0, 0, 255)
        if status == "occluded":
            return (0, 165, 255)
        return (0, 180, 0)
