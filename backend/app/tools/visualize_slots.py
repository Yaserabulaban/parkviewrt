import json
from pathlib import Path
import cv2


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
IMAGE_DIR = BASE_DIR / "data" / "images"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def draw_slots(location_id: str):
    image_path = IMAGE_DIR / f"{location_id}.jpeg"
    slots_path = SLOTS_DIR / f"{location_id}_slots.json"

    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(slots_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for slot in data["slots"]:
        points = slot["points"]
        slot_id = slot["slot_id"]

        polygon = cv2.UMat(
            cv2.convexHull(
                cv2.UMat(
                    __import__("numpy").array(points, dtype="int32")
                ).get()
            )
        ).get()

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

    output_path = OUTPUT_DIR / f"{location_id}_slots_preview.jpg"
    cv2.imwrite(str(output_path), image)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    draw_slots("fci")
    draw_slots("faie")