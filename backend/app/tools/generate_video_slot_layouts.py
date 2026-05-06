import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SLOTS_DIR = BASE_DIR / "data" / "slots"


def point_between(start: tuple[float, float], end: tuple[float, float], ratio: float):
    return [
        round(start[0] + (end[0] - start[0]) * ratio, 2),
        round(start[1] + (end[1] - start[1]) * ratio, 2),
    ]


def build_row(
    prefix: str,
    start_index: int,
    count: int,
    top_left: tuple[float, float],
    top_right: tuple[float, float],
    bottom_left: tuple[float, float],
    bottom_right: tuple[float, float],
    gap_ratio: float = 0.14,
):
    slots = []
    for index in range(count):
        left_ratio = (index + gap_ratio) / count
        right_ratio = (index + 1 - gap_ratio) / count
        slots.append(
            {
                "slot_id": f"{prefix}{start_index + index}",
                "row": prefix,
                "shape": "polygon",
                "points": [
                    point_between(top_left, top_right, left_ratio),
                    point_between(top_left, top_right, right_ratio),
                    point_between(bottom_left, bottom_right, right_ratio),
                    point_between(bottom_left, bottom_right, left_ratio),
                ],
            }
        )

    return slots


def build_fci_slots():
    slots = []

    slots.extend(
        build_row(
            "A",
            1,
            6,
            top_left=(-5, 515),
            top_right=(375, 500),
            bottom_left=(-5, 620),
            bottom_right=(380, 605),
            gap_ratio=0.16,
        )
    )
    slots.extend(
        build_row(
            "A",
            7,
            20,
            top_left=(560, 545),
            top_right=(1585, 455),
            bottom_left=(575, 715),
            bottom_right=(1585, 585),
            gap_ratio=0.16,
        )
    )
    slots.extend(
        build_row(
            "A",
            27,
            20,
            top_left=(0, 655),
            top_right=(960, 620),
            bottom_left=(0, 900),
            bottom_right=(980, 780),
            gap_ratio=0.16,
        )
    )
    slots.extend(
        build_row(
            "A",
            47,
            20,
            top_left=(520, 900),
            top_right=(1435, 780),
            bottom_left=(535, 1080),
            bottom_right=(1455, 1005),
            gap_ratio=0.16,
        )
    )
    slots.extend(
        build_row(
            "A",
            67,
            14,
            top_left=(1360, 690),
            top_right=(1920, 665),
            bottom_left=(1375, 880),
            bottom_right=(1920, 835),
            gap_ratio=0.14,
        )
    )

    slots = [slot for slot in slots if slot["slot_id"] != "A77"]

    return {
        "location_id": "fci",
        "layout_type": "video_day_frame",
        "slots": slots,
    }


def build_faie_slots():
    slots = []

    slots.extend(
        build_row(
            "B",
            1,
            25,
            top_left=(0, 360),
            top_right=(1920, 590),
            bottom_left=(0, 425),
            bottom_right=(1920, 775),
            gap_ratio=0.2,
        )
    )
    slots.extend(
        build_row(
            "B",
            26,
            5,
            top_left=(0, 620),
            top_right=(500, 625),
            bottom_left=(0, 790),
            bottom_right=(500, 760),
            gap_ratio=0.18,
        )
    )
    slots.extend(
        build_row(
            "B",
            31,
            10,
            top_left=(460, 790),
            top_right=(1320, 1000),
            bottom_left=(460, 1080),
            bottom_right=(1345, 1080),
            gap_ratio=0.2,
        )
    )

    return {
        "location_id": "faie",
        "layout_type": "video_day_frame",
        "slots": slots,
    }


def write_layout(file_name: str, layout: dict):
    output_path = SLOTS_DIR / file_name
    output_path.write_text(
        json.dumps(layout, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {output_path} ({len(layout['slots'])} slots)")


if __name__ == "__main__":
    write_layout("fci_slots.json", build_fci_slots())
    write_layout("faie_slots.json", build_faie_slots())
