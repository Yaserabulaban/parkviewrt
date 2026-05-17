from pathlib import Path

from slot_generation import build_slot_layout, save_slot_layout

BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"

FAIE_DAY_ANNOTATION_ORDER = [
    *range(1, 16),
    21,
    22,
    20,
    19,
    18,
    17,
    16,
]

VARIANTS = {
    "day": {
        "annotation_path": SLOTS_DIR / "faie_day_annotations.json",
        "output_path": SLOTS_DIR / "faie_day_slots.json",
        "layout_type": "video_day_frame",
        "annotation_order": FAIE_DAY_ANNOTATION_ORDER,
    },
    "night": {
        "annotation_path": SLOTS_DIR / "faie_night_annotations.json",
        "output_path": SLOTS_DIR / "faie_night_slots.json",
        "layout_type": "video_night_frame",
    },
}


def build_faie_slots(variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError("variant must be either day or night")

    variant_config = VARIANTS[variant]
    return build_slot_layout(
        location_id="faie",
        row="B",
        slot_prefix="B",
        layout_type=variant_config["layout_type"],
        annotation_path=variant_config["annotation_path"],
        location_label=f"FAIE {variant}",
        annotation_order=variant_config.get("annotation_order"),
    )


def save_faie_slots(variant: str) -> tuple[Path, int]:
    layout = build_faie_slots(variant)
    path = save_slot_layout(layout, VARIANTS[variant]["output_path"])
    return path, len(layout["slots"])


if __name__ == "__main__":
    for variant in VARIANTS:
        path, slot_count = save_faie_slots(variant)
        print(f"Saved {path} ({slot_count} slots)")
