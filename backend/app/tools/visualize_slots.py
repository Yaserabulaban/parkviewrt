import json
from pathlib import Path

import cv2
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
IMAGE_DIR = BASE_DIR / "data" / "images"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_image_path(location_id: str, variant: str) -> Path:
    for extension in (".jpg", ".jpeg", ".png"):
        image_path = IMAGE_DIR / f"{location_id}_{variant}{extension}"
        if image_path.exists():
            return image_path

    raise FileNotFoundError(f"Image not found for location: {location_id}, variant: {variant}")


def draw_slots(location_id: str, variant: str):
    image_path = find_image_path(location_id, variant)
    slots_path = SLOTS_DIR / f"{location_id}_{variant}_slots.json"
    if not slots_path.exists():
        raise FileNotFoundError(f"Slot file not found: {slots_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(slots_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for slot in data["slots"]:
        points = slot["points"]
        slot_id = slot["slot_id"]

        polygon = cv2.convexHull(np.array(points, dtype="int32"))

        cv2.polylines(image, [polygon], True, (0, 255, 0), 2)

        x, y = points[0]
        cv2.putText(
            image,
            slot_id,
            (int(x), int(y) - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    output_path = OUTPUT_DIR / f"{location_id}_{variant}_slots_preview.jpg"
    cv2.imwrite(str(output_path), image)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    for location in ("fci", "faie"):
        for video_variant in ("day", "night"):
            draw_slots(location, video_variant)
