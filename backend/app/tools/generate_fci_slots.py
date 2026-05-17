from pathlib import Path

from slot_generation import build_slot_layout, save_slot_layout


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"

# Label Studio exports annotations by creation order. This order maps the
# FCI day polygons into the parking-row order used by the dashboard.
FCI_DAY_ANNOTATION_ROW_ORDER = [
    [1, 2, 3, 4, 5, 6],
    [7, 8, 9, 15, 17, 20, 21, 23, 25, 27, 29, 31, 33, 34, 38, 39, 41, 42, 47],
    [11, 10, 12, 13, 14, 16, 18, 19, 22, 24, 26, 28, 30, 32, 35, 36, 37, 40, 43, 44, 45, 46],
    [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65],
    [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78],
]

# Label Studio exports annotations by creation order. This order maps the
# FCI night polygons into the parking-row order used by the dashboard.
FCI_NIGHT_ANNOTATION_ROW_ORDER = [
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

VARIANTS = {
    "day": {
        "annotation_path": SLOTS_DIR / "fci_day_annotations.json",
        "output_path": SLOTS_DIR / "fci_day_slots.json",
        "layout_type": "video_day_frame",
        "annotation_order": [
            index for row in FCI_DAY_ANNOTATION_ROW_ORDER for index in row
        ],
    },
    "night": {
        "annotation_path": SLOTS_DIR / "fci_night_annotations.json",
        "output_path": SLOTS_DIR / "fci_night_slots.json",
        "layout_type": "video_night_frame",
        "annotation_order": [
            index for row in FCI_NIGHT_ANNOTATION_ROW_ORDER for index in row
        ],
    },
}


def build_fci_slots(variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError("variant must be either day or night")

    variant_config = VARIANTS[variant]
    return build_slot_layout(
        location_id="fci",
        row="A",
        slot_prefix="A",
        layout_type=variant_config["layout_type"],
        annotation_path=variant_config["annotation_path"],
        location_label=f"FCI {variant}",
        annotation_order=variant_config.get("annotation_order"),
    )


def save_fci_slots(variant: str) -> tuple[Path, int]:
    layout = build_fci_slots(variant)
    path = save_slot_layout(layout, VARIANTS[variant]["output_path"])
    return path, len(layout["slots"])


if __name__ == "__main__":
    for variant in VARIANTS:
        path, slot_count = save_fci_slots(variant)
        print(f"Saved {path} ({slot_count} slots)")
