import json
from pathlib import Path


def annotation_points(annotation: dict) -> list[list[float]]:
    coordinates = annotation["segmentation"][0]
    return [
        [round(coordinates[index], 2), round(coordinates[index + 1], 2)]
        for index in range(0, len(coordinates), 2)
    ]


def make_slot(slot_id: str, row: str, points: list[list[float]]) -> dict:
    return {
        "slot_id": slot_id,
        "row": row,
        "shape": "polygon",
        "points": points,
    }


def ordered_annotations(
    annotation_path: Path,
    location_label: str,
    annotation_order: list[int] | None = None,
) -> list[dict]:
    exported_data = json.loads(annotation_path.read_text(encoding="utf-8"))
    annotations = exported_data["annotations"]
    if not annotations:
        raise ValueError(f"No {location_label} annotations found")

    if annotation_order is None:
        return sorted(annotations, key=lambda annotation: annotation["id"])

    annotations_by_number = {
        annotation["id"] + 1: annotation for annotation in annotations
    }
    missing_indexes = sorted(set(annotation_order) - set(annotations_by_number))
    if missing_indexes:
        raise ValueError(f"Missing {location_label} annotations: {missing_indexes}")
    if len(annotation_order) != len(set(annotation_order)):
        raise ValueError(f"{location_label} annotation order contains duplicate indexes")
    if len(annotation_order) != len(annotations_by_number):
        unused_indexes = sorted(set(annotations_by_number) - set(annotation_order))
        raise ValueError(f"Unused {location_label} annotations: {unused_indexes}")

    return [annotations_by_number[index] for index in annotation_order]


def build_slot_layout(
    *,
    location_id: str,
    row: str,
    slot_prefix: str,
    layout_type: str,
    annotation_path: Path,
    location_label: str,
    annotation_order: list[int] | None = None,
    slot_ids: list[str] | None = None,
) -> dict:
    annotations = ordered_annotations(
        annotation_path,
        location_label,
        annotation_order=annotation_order,
    )
    resolved_slot_ids = slot_ids or [
        f"{slot_prefix}{slot_number}"
        for slot_number in range(1, len(annotations) + 1)
    ]
    if len(resolved_slot_ids) != len(annotations):
        raise ValueError(
            f"{location_label} has {len(annotations)} annotations but "
            f"{len(resolved_slot_ids)} runtime slot ids"
        )
    if len(resolved_slot_ids) != len(set(resolved_slot_ids)):
        raise ValueError(f"{location_label} runtime slot ids contain duplicates")

    slots = [
        make_slot(
            slot_id,
            row,
            annotation_points(annotation),
        )
        for slot_id, annotation in zip(resolved_slot_ids, annotations)
    ]

    return {
        "location_id": location_id,
        "layout_type": layout_type,
        "slots": slots,
    }


def save_slot_layout(layout: dict, output_path: Path) -> Path:
    output_path.write_text(json.dumps(layout, indent=2), encoding="utf-8")
    return output_path
