import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"
ANNOTATION_PATH = SLOTS_DIR / "fci_night_annotations.json"
OUTPUT_PATH = SLOTS_DIR / "fci_night_slots.json"

# Label Studio exports annotations by creation order. This order maps those
# hand-drawn polygons into the parking-row order used by the dashboard.
ANNOTATION_ROW_ORDER = [
    [1, 2, 3, 4, 5, 6],
    [7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 12, 26, 27, 28, 29, 30, 31, 32, 33],
    [
        51,
        50,
        49,
        48,
        47,
        46,
        45,
        10,
        9,
        44,
        43,
        11,
        42,
        41,
        40,
        39,
        37,
        35,
        36,
        38,
        34,
        14,
        66,
        67,
    ],
    [52, 53, 54, 55, 56, 57, 58, 59, 60, 13, 61, 62, 63, 64, 65],
    [68, 69, 16, 70, 71, 72, 73, 74, 15, 75, 76, 77],
]


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


def ordered_annotation_indexes() -> list[int]:
    return [index for row in ANNOTATION_ROW_ORDER for index in row]


def build_fci_night_slots() -> dict:
    exported_data = json.loads(ANNOTATION_PATH.read_text(encoding="utf-8"))
    annotations_by_number = {
        annotation["id"] + 1: annotation for annotation in exported_data["annotations"]
    }
    ordered_indexes = ordered_annotation_indexes()

    missing_indexes = sorted(set(ordered_indexes) - set(annotations_by_number))
    if missing_indexes:
        raise ValueError(f"Missing FCI night annotations: {missing_indexes}")
    if len(ordered_indexes) != len(set(ordered_indexes)):
        raise ValueError("FCI night annotation order contains duplicate indexes")
    if len(ordered_indexes) != len(annotations_by_number):
        unused_indexes = sorted(set(annotations_by_number) - set(ordered_indexes))
        raise ValueError(f"Unused FCI night annotations: {unused_indexes}")

    slots = [
        make_slot(f"A{slot_number}", annotation_points(annotations_by_number[index]))
        for slot_number, index in enumerate(ordered_indexes, start=1)
    ]

    return {
        "location_id": "fci",
        "layout_type": "video_night_frame",
        "slots": slots,
    }


if __name__ == "__main__":
    layout = build_fci_night_slots()
    OUTPUT_PATH.write_text(json.dumps(layout, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH} ({len(layout['slots'])} slots)")
