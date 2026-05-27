from pathlib import Path

from slot_generation import build_slot_layout, save_slot_layout

BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"

FAIE_DAY_RUNTIME_SLOT_IDS = [
    *[f"B{index}" for index in range(1, 17)],
    *[f"B{index}" for index in range(24, 32)],
]
FAIE_NIGHT_RUNTIME_SLOT_IDS = [
    *[f"B{index}" for index in range(1, 16)],
    *[f"B{index}" for index in range(24, 27)],
]
FAIE_NIGHT_ANNOTATION_ORDER = [
    6,
    5,
    4,
    3,
    2,
    1,
    *range(7, 19),
]

VARIANTS = {
    "day": {
        "annotation_path": SLOTS_DIR / "faie_day_annotations.json",
        "output_path": SLOTS_DIR / "faie_day_slots.json",
        "layout_type": "video_day_frame",
        "slot_ids": FAIE_DAY_RUNTIME_SLOT_IDS,
    },
    "night": {
        "annotation_path": SLOTS_DIR / "faie_night_annotations.json",
        "output_path": SLOTS_DIR / "faie_night_slots.json",
        "layout_type": "video_night_frame",
        "annotation_order": FAIE_NIGHT_ANNOTATION_ORDER,
        "slot_ids": FAIE_NIGHT_RUNTIME_SLOT_IDS,
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
        slot_ids=variant_config.get("slot_ids"),
    )


def save_faie_slots(variant: str) -> tuple[Path, int]:
    layout = build_faie_slots(variant)
    path = save_slot_layout(layout, VARIANTS[variant]["output_path"])
    return path, len(layout["slots"])


if __name__ == "__main__":
    for variant in VARIANTS:
        path, slot_count = save_faie_slots(variant)
        print(f"Saved {path} ({slot_count} slots)")
