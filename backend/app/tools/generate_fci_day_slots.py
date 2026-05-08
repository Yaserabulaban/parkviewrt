import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
ANNOTATION_PATH = SLOTS_DIR / "fci_day_annotations.json"
OUTPUT_PATH = SLOTS_DIR / "fci_day_slots.json"


def annotation_points(annotation: dict) -> list[list[float]]:
    coordinates = annotation["segmentation"][0]
    return [
        [round(coordinates[index], 2), round(coordinates[index + 1], 2)]
        for index in range(0, len(coordinates), 2)
    ]


def make_slot(slot_id: str, points: list[list[float]]) -> dict:
    return {
        "slot_id": slot_id,
        "row": "A",
        "shape": "polygon",
        "points": points,
    }


def build_fci_day_slots() -> dict:
    exported_data = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    annotations = sorted(exported_data["annotations"], key=lambda annotation: annotation["id"])
    if not annotations:
        raise ValueError("No FCI day annotations found")

    slots = [
        make_slot(f"A{slot_number}", annotation_points(annotation))
        for slot_number, annotation in enumerate(annotations, start=1)
    ]

    return {
        "location_id": "fci",
        "layout_type": "video_day_frame",
        "slots": slots,
    }


if __name__ == "__main__":
    layout = build_fci_day_slots()
    OUTPUT_PATH.write_text(json.dumps(layout, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH} ({len(layout['slots'])} slots)")
