import random


PARKING_SLOT_LAYOUTS = {
    "fci": {
        "display_slot_ids": [f"A{index}" for index in range(1, 79)],
        "monitored_slot_ids": [f"A{index}" for index in range(1, 79)],
        "default_variant": "day",
        "variants": {
            "day": {
                "display_slot_ids": [f"A{index}" for index in range(1, 79)],
                "monitored_slot_ids": [f"A{index}" for index in range(1, 79)],
            },
            "night": {
                "display_slot_ids": [f"A{index}" for index in range(1, 78)],
                "monitored_slot_ids": [f"A{index}" for index in range(1, 78)],
            },
        },
    },
    "faie": {
        "display_slot_ids": [f"B{index}" for index in range(1, 41)],
        "monitored_slot_ids": [f"B{index}" for index in range(1, 23)],
        "default_variant": "day",
        "variants": {
            "day": {
                "display_slot_ids": [f"B{index}" for index in range(1, 41)],
                "monitored_slot_ids": [f"B{index}" for index in range(1, 23)],
            },
            "night": {
                "display_slot_ids": [f"B{index}" for index in range(1, 41)],
                "monitored_slot_ids": [f"B{index}" for index in range(1, 19)],
            },
        },
    },
}


def build_demo_parking_status(
    location_id: str,
    variant: str | None = None,
    occupancy_rate: float = 0.5,
    seed: int | None = None,
) -> dict:
    normalized_location_id = location_id.lower()
    if normalized_location_id not in PARKING_SLOT_LAYOUTS:
        raise ValueError(f"Unknown location: {location_id}")

    if occupancy_rate < 0 or occupancy_rate > 1:
        raise ValueError("occupancy_rate must be between 0 and 1")

    slot_layout = PARKING_SLOT_LAYOUTS[normalized_location_id]
    if variant:
        normalized_variant = variant.lower()
        if normalized_variant not in slot_layout.get("variants", {}):
            raise ValueError("variant must be either day or night")
        slot_layout = slot_layout["variants"][normalized_variant]

    generator = random.Random(seed)
    slots = [
        {
            "slot_id": slot_id,
            "occupied": generator.random() < occupancy_rate,
        }
        for slot_id in slot_layout["display_slot_ids"]
    ]
    for slot in slots:
        slot["status"] = "occupied" if slot["occupied"] else "available"

    occupied_count = sum(1 for slot in slots if slot["occupied"])
    total_slots = len(slots)

    return {
        "location_id": normalized_location_id,
        "total_slots": total_slots,
        "occupied_count": occupied_count,
        "available_count": total_slots - occupied_count,
        "occluded_count": 0,
        "slots": slots,
    }
