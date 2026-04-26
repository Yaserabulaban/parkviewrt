import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box

from app.services.yolo_detector import get_yolo_detector


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
IMAGES_DIR = BASE_DIR / "data" / "images"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
VALID_LOCATION_IDS = {"fci", "faie"}


class ParkingOccupancyService:
    def __init__(self, overlap_threshold: float = 0.30):
        self.overlap_threshold = overlap_threshold
        self.detector = get_yolo_detector()

    def get_status(self, location_id: str) -> dict:
        analysis = self._analyze_location(location_id)
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

    def create_debug_image(self, location_id: str) -> Path:
        analysis = self._analyze_location(location_id)
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

    def _analyze_location(self, location_id: str) -> dict:
        normalized_location_id = location_id.lower()
        slot_data = self._load_slots(normalized_location_id)
        image_path = self._get_image_path(normalized_location_id)
        detections = self.detector.detect_cars(image_path)
        slots = self._calculate_slot_occupancy(slot_data["slots"], detections)

        return {
            "location_id": slot_data.get("location_id", normalized_location_id),
            "slot_data": slot_data,
            "image_path": image_path,
            "detections": detections,
            "slots": slots,
        }

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

    def _calculate_slot_occupancy(self, slots: list[dict], detections: list[dict]) -> list[dict]:
        occupancy_results = []

        for slot in slots:
            slot_polygon = Polygon(slot["points"])
            slot_area = slot_polygon.area
            best_overlap_ratio = 0
            occupied = False

            if slot_area > 0:
                for detection in detections:
                    detection_box = box(*detection["bbox"])
                    intersection_area = slot_polygon.intersection(detection_box).area
                    overlap_ratio = intersection_area / slot_area
                    best_overlap_ratio = max(best_overlap_ratio, overlap_ratio)

                    if overlap_ratio > self.overlap_threshold:
                        occupied = True

            occupancy_results.append(
                {
                    "slot_id": slot["slot_id"],
                    "occupied": occupied,
                    "overlap_ratio": best_overlap_ratio,
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
            label = f"{slot['slot_id']} {slot_status['overlap_ratio']:.0%}"

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
            f"available: {available_count} | cars detected: {detection_count}"
        )

        cv2.rectangle(image, (20, 20), (980, 72), (0, 0, 0), -1)
        cv2.putText(
            image,
            summary,
            (35, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (255, 255, 255),
            2,
        )
