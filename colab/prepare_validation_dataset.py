import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GROUND_TRUTH_DIR = PROJECT_ROOT / "colab" / "ground_truth"
DEFAULT_EXISTING_GROUND_TRUTH = GROUND_TRUTH_DIR / "slot_status_ground_truth.csv"
DEFAULT_GROUND_TRUTH = GROUND_TRUTH_DIR / "slot_status_ground_truth.csv"
DEFAULT_SELECTION_SUMMARY = GROUND_TRUTH_DIR / "frame_selection_summary.csv"
DEFAULT_REVIEW_DIR = (
    PROJECT_ROOT / "colab" / "outputs" / "validation" / "review_images"
)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.occupancy import ParkingOccupancyService  # noqa: E402
from app.services.video_snapshot import VideoSnapshotService  # noqa: E402


VARIANTS = (
    ("fci", "day"),
    ("fci", "night"),
    ("faie", "day"),
    ("faie", "night"),
)
# Eleven equally spaced positions include 0%, 10%, ..., 100%. If an endpoint
# frame is blank or unreadable, read_usable_frame moves to the nearest usable
# frame and records that adjustment in the selection summary.
FRAME_FRACTIONS = tuple(index / 10 for index in range(11))
VALID_STATUSES = {"available", "occupied", "occluded"}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows were generated for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_existing_labels(path: Path) -> tuple[dict[tuple, dict], dict[tuple, list[int]]]:
    labels = {}
    frame_indices = defaultdict(list)
    for row in read_csv(path):
        status = (row.get("expected_status") or row.get("status") or "").lower()
        if status not in VALID_STATUSES:
            continue
        key = (
            row["location_id"].lower(),
            row["variant"].lower(),
            int(row["frame_index"]),
            row["slot_id"],
        )
        verification_status = row.get("verification_status", "verified")
        labels[key] = {
            "status": status,
            "verification_status": verification_status,
            "label_source": row.get("label_source", "active_ground_truth"),
            "notes": row.get("notes", "retained from the active ground-truth CSV"),
        }
        frame_key = key[:2]
        if (
            verification_status == "verified"
            and key[2] not in frame_indices[frame_key]
        ):
            frame_indices[frame_key].append(key[2])
    return labels, dict(frame_indices)


def choose_target_frame(
    frame_count: int,
    fraction: float,
    existing_indices: list[int],
) -> tuple[int, str]:
    target = int((frame_count - 1) * fraction)
    if existing_indices:
        nearest = min(existing_indices, key=lambda value: abs(value - target))
        tolerance = max(3, int(frame_count * 0.00025))
        if abs(nearest - target) <= tolerance:
            return nearest, "reviewed_frame_near_even_target"
    return target, "evenly_spaced_across_video"


def read_usable_frame(
    video_service: VideoSnapshotService,
    video_path: Path,
    requested_index: int,
    frame_count: int,
) -> tuple[np.ndarray, int]:
    offsets = [0]
    for distance in range(1, 61):
        offsets.extend((distance, -distance))

    for offset in offsets:
        candidate = min(max(requested_index + offset, 0), frame_count - 1)
        frame, actual_index = video_service._read_frame(video_path, candidate)
        if frame is None or frame.size == 0:
            continue
        if float(frame.mean()) <= 2.0 or float(frame.std()) <= 2.0:
            continue
        return frame, actual_index
    raise ValueError(
        f"Unable to find a usable frame near {requested_index} in {video_path}"
    )


def save_review_image(
    service: ParkingOccupancyService,
    analysis: dict,
    frame: np.ndarray,
    output_path: Path,
) -> None:
    image = frame.copy()
    slot_lookup = {slot["slot_id"]: slot for slot in analysis["slots"]}
    service._draw_slots(image, analysis["slot_data"]["slots"], slot_lookup)
    service._draw_detections(image, analysis["detections"])
    service._draw_summary(image, analysis)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def build_selection(
    service: ParkingOccupancyService,
    video_service: VideoSnapshotService,
    existing_frames: dict[tuple, list[int]],
    review_dir: Path,
) -> tuple[list[dict], list[dict]]:
    selection_rows = []
    prepared_frames = []

    requested = [
        (location_id, variant, fraction)
        for location_id, variant in VARIANTS
        for fraction in FRAME_FRACTIONS
    ]

    for location_id, variant, fraction in requested:
        video_path = video_service._find_video_path(location_id, variant)
        metadata = video_service._get_video_metadata(video_path)
        frame_count = metadata["frame_count"]
        fps = metadata["fps"]
        target_index, method = choose_target_frame(
            frame_count,
            fraction,
            existing_frames.get((location_id, variant), []),
        )
        frame, actual_index = read_usable_frame(
            video_service,
            video_path,
            target_index,
            frame_count,
        )
        if actual_index != target_index:
            method = f"{method}; shifted_to_nearest_usable_frame"

        analysis = service._analyze_location(
            location_id,
            image_source=frame,
            variant=variant,
        )
        frame_id = f"{location_id}_{variant}_{actual_index}"
        review_path = review_dir / f"{frame_id}_debug.jpg"
        save_review_image(service, analysis, frame, review_path)

        selection_rows.append(
            {
                "frame_id": frame_id,
                "location_id": location_id,
                "variant": variant,
                "video_path": str(video_path.relative_to(PROJECT_ROOT)),
                "frame_index": actual_index,
                "timestamp_seconds": f"{actual_index / fps:.3f}",
                "frame_source": "original_source_video",
                "selection_role": "regular",
                "target_fraction": f"{fraction:.2f}",
                "selection_method": method,
                "review_image": str(review_path.relative_to(PROJECT_ROOT)),
            }
        )
        prepared_frames.append(
            {
                "frame_id": frame_id,
                "location_id": location_id,
                "variant": variant,
                "frame_index": actual_index,
                "analysis": analysis,
            }
        )
        print(
            f"Prepared {frame_id}: {len(analysis['slots'])} monitored slots "
            "(regular)"
        )

    return selection_rows, prepared_frames


def build_ground_truth_rows(
    prepared_frames: list[dict],
    existing_labels: dict[tuple, dict],
) -> list[dict]:
    rows = []
    for prepared in prepared_frames:
        for slot in prepared["analysis"]["slots"]:
            key = (
                prepared["location_id"],
                prepared["variant"],
                prepared["frame_index"],
                slot["slot_id"],
            )
            existing = existing_labels.get(key)
            if existing:
                status = existing["status"]
                verification_status = existing["verification_status"]
                label_source = existing["label_source"]
                notes = existing["notes"]
            else:
                status = slot["status"]
                verification_status = "preliminary"
                label_source = "yolo11n_assisted_current_thresholds"
                notes = "manual review required using the matching debug image"

            rows.append(
                {
                    "frame_id": prepared["frame_id"],
                    "location_id": prepared["location_id"],
                    "variant": prepared["variant"],
                    "frame_index": prepared["frame_index"],
                    "slot_id": slot["slot_id"],
                    "status": status,
                    "expected_status": status,
                    "verification_status": verification_status,
                    "label_source": label_source,
                    "notes": notes,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Select 11 evenly spaced frames per ParkViewRT video variant and "
            "prepare assisted slot labels for manual review."
        )
    )
    parser.add_argument(
        "--existing-ground-truth",
        type=Path,
        default=DEFAULT_EXISTING_GROUND_TRUTH,
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GROUND_TRUTH,
    )
    parser.add_argument(
        "--selection-summary",
        type=Path,
        default=DEFAULT_SELECTION_SUMMARY,
    )
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    args = parser.parse_args()

    existing_labels, existing_frames = load_existing_labels(
        args.existing_ground_truth
    )
    service = ParkingOccupancyService()
    video_service = VideoSnapshotService(service)
    selection_rows, prepared_frames = build_selection(
        service,
        video_service,
        existing_frames,
        args.review_dir,
    )
    ground_truth_rows = build_ground_truth_rows(prepared_frames, existing_labels)

    write_csv(args.selection_summary, selection_rows)
    write_csv(args.ground_truth, ground_truth_rows)

    verified = sum(
        row["verification_status"] == "verified" for row in ground_truth_rows
    )
    preliminary = len(ground_truth_rows) - verified
    print(f"Saved: {args.selection_summary}")
    print(f"Saved: {args.ground_truth}")
    print(
        f"Prepared {len(selection_rows)} frames and {len(ground_truth_rows)} labels: "
        f"{verified} verified, {preliminary} preliminary."
    )


if __name__ == "__main__":
    main()
