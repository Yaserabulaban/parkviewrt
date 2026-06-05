import argparse
import csv
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MODEL_DIR = BACKEND_DIR / "app" / "models"
DEFAULT_GROUND_TRUTH_PATH = (
    PROJECT_ROOT / "colab" / "ground_truth" / "slot_status_ground_truth.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "colab" / "outputs"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.settings import AppSettings, DetectionSettings, get_settings  # noqa: E402
from app.services.occupancy import ParkingOccupancyService  # noqa: E402
from app.services.video_snapshot import VideoSnapshotService  # noqa: E402


VALID_STATUSES = {"occupied", "available", "occluded"}


def parse_grid(raw_values: str) -> list[float]:
    return [float(value.strip()) for value in raw_values.split(",") if value.strip()]


def resolve_model_path(model_name: str) -> Path:
    model_path = Path(model_name)
    if model_path.is_absolute():
        return model_path
    if model_path.parent != Path("."):
        return PROJECT_ROOT / model_path
    return MODEL_DIR / model_name


def build_settings(model_path: Path) -> AppSettings:
    current = get_settings().detection
    detection = DetectionSettings(
        model_path=model_path,
        confidence_threshold=current.confidence_threshold,
        image_size=current.image_size,
        slot_overlap_threshold=current.slot_overlap_threshold,
        box_overlap_threshold=current.box_overlap_threshold,
    )
    return AppSettings(detection=detection)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV file: {path}")
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_ground_truth(path: Path) -> dict[str, list[dict]]:
    grouped_rows = defaultdict(list)
    for row in read_csv(path):
        expected_status = row["expected_status"].strip().lower()
        if expected_status not in VALID_STATUSES:
            raise ValueError(
                f"{path} has invalid expected_status={row['expected_status']!r} "
                f"for frame_id={row['frame_id']} slot_id={row['slot_id']}"
            )
        row["expected_status"] = expected_status
        grouped_rows[row["frame_id"]].append(row)
    return dict(grouped_rows)


def precision_recall_f1(confusion: Counter, status: str) -> dict[str, float]:
    true_positive = confusion[(status, status)]
    false_positive = sum(
        count
        for (expected, predicted), count in confusion.items()
        if expected != status and predicted == status
    )
    false_negative = sum(
        count
        for (expected, predicted), count in confusion.items()
        if expected == status and predicted != status
    )
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def load_frame_data(
    service: ParkingOccupancyService,
    video_service: VideoSnapshotService,
    ground_truth: dict[str, list[dict]],
) -> dict[str, dict]:
    frame_data = {}
    for frame_id, expected_rows in ground_truth.items():
        first_row = expected_rows[0]
        location_id = first_row["location_id"]
        variant = first_row["variant"]
        frame_index = int(first_row["frame_index"])
        video_path = video_service._find_video_path(location_id, variant)
        frame, actual_frame_index = video_service._read_frame(video_path, frame_index)
        if actual_frame_index != frame_index:
            raise ValueError(
                f"Requested frame {frame_index}, but video returned frame {actual_frame_index}"
            )

        frame_data[frame_id] = {
            "frame_id": frame_id,
            "location_id": location_id,
            "variant": variant,
            "frame_index": frame_index,
            "frame": frame,
            "slot_data": service._load_slots(location_id, variant),
            "expected_rows": expected_rows,
        }
    return frame_data


def detect_for_confidence(
    service: ParkingOccupancyService,
    frame_data: dict[str, dict],
    confidence: float,
) -> dict[str, dict]:
    # YOLO inference is the slow part of tuning. Run it once for each
    # confidence threshold, then reuse those detections while sweeping the
    # cheaper polygon-overlap thresholds.
    detections_by_frame = {}
    for frame_id, data in frame_data.items():
        start_time = time.perf_counter()
        detections = service.detector.detect_vehicles(
            data["frame"],
            confidence_threshold=confidence,
            image_size=service.image_size,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        detections_by_frame[frame_id] = {
            "detections": detections,
            "elapsed_ms": elapsed_ms,
        }
    return detections_by_frame


def evaluate_thresholds(
    service: ParkingOccupancyService,
    frame_data: dict[str, dict],
    detections_by_frame: dict[str, dict],
    confidence: float,
    slot_threshold: float,
    box_threshold: float,
) -> tuple[dict, list[dict]]:
    slot_rows = []
    frame_rows = []

    for frame_id, data in frame_data.items():
        detection_data = detections_by_frame[frame_id]
        slots = service._calculate_slot_occupancy(
            data["slot_data"]["slots"],
            detection_data["detections"],
            overlap_threshold=slot_threshold,
            box_overlap_threshold=box_threshold,
        )
        service._apply_known_occlusions(data["location_id"], data["variant"], slots)
        prediction_lookup = {slot["slot_id"]: slot for slot in slots}
        frame_correct = 0

        for expected_row in data["expected_rows"]:
            slot_id = expected_row["slot_id"]
            expected_status = expected_row["expected_status"]
            predicted_status = prediction_lookup[slot_id]["status"]
            correct = expected_status == predicted_status
            if correct:
                frame_correct += 1
            slot_rows.append(
                {
                    "frame_id": frame_id,
                    "location_id": data["location_id"],
                    "variant": data["variant"],
                    "frame_index": data["frame_index"],
                    "slot_id": slot_id,
                    "expected_status": expected_status,
                    "predicted_status": predicted_status,
                    "correct": str(correct).lower(),
                    "occupied_reason": prediction_lookup[slot_id]["occupied_reason"],
                }
            )

        frame_rows.append(
            {
                "frame_id": frame_id,
                "location_id": data["location_id"],
                "variant": data["variant"],
                "frame_index": data["frame_index"],
                "slots": len(data["expected_rows"]),
                "correct_slots": frame_correct,
                "detections": len(detection_data["detections"]),
                "inference_ms": detection_data["elapsed_ms"],
            }
        )

    total_slots = len(slot_rows)
    correct_slots = sum(row["correct"] == "true" for row in slot_rows)
    confusion = Counter(
        (row["expected_status"], row["predicted_status"]) for row in slot_rows
    )
    occupied = precision_recall_f1(confusion, "occupied")
    available = precision_recall_f1(confusion, "available")
    occluded = precision_recall_f1(confusion, "occluded")
    false_available = sum(
        row["predicted_status"] == "available"
        and row["expected_status"] in {"occupied", "occluded"}
        for row in slot_rows
    )
    false_occupied = sum(
        row["predicted_status"] == "occupied"
        and row["expected_status"] in {"available", "occluded"}
        for row in slot_rows
    )
    false_occluded = sum(
        row["predicted_status"] == "occluded"
        and row["expected_status"] in {"occupied", "available"}
        for row in slot_rows
    )

    summary = {
        "model": "yolo11n.pt",
        "confidence_threshold": confidence,
        "slot_overlap_threshold": slot_threshold,
        "box_overlap_threshold": box_threshold,
        "frames": len(frame_rows),
        "slots": total_slots,
        "correct_slots": correct_slots,
        "accuracy": correct_slots / total_slots if total_slots else 0.0,
        "occupied_precision": occupied["precision"],
        "occupied_recall": occupied["recall"],
        "occupied_f1": occupied["f1"],
        "available_precision": available["precision"],
        "available_recall": available["recall"],
        "available_f1": available["f1"],
        "occluded_precision": occluded["precision"],
        "occluded_recall": occluded["recall"],
        "occluded_f1": occluded["f1"],
        "false_available": false_available,
        "false_occupied": false_occupied,
        "false_occluded": false_occluded,
        "detections_mean": mean(row["detections"] for row in frame_rows),
        "inference_ms_mean": mean(row["inference_ms"] for row in frame_rows),
    }
    mismatches = [
        {
            "confidence_threshold": confidence,
            "slot_overlap_threshold": slot_threshold,
            "box_overlap_threshold": box_threshold,
            **row,
        }
        for row in slot_rows
        if row["correct"] == "false"
    ]
    return summary, mismatches


def rank_key(row: dict) -> tuple:
    # Prefer safety before strict speed: an occupied slot incorrectly marked
    # available is worse for the dashboard than a conservative occupied/occluded
    # result. Ties keep the current moderate thresholds near the top.
    return (
        row["accuracy"],
        row["occupied_recall"],
        row["available_recall"],
        row["occluded_recall"],
        -row["false_available"],
        -row["false_occupied"],
        -row["false_occluded"],
        -row["confidence_threshold"],
        row["slot_overlap_threshold"],
        row["box_overlap_threshold"],
    )


def run_tuning(
    model_name: str,
    confidence_values: list[float],
    slot_values: list[float],
    box_values: list[float],
    ground_truth_path: Path,
) -> tuple[list[dict], list[dict]]:
    model_path = resolve_model_path(model_name)
    service = ParkingOccupancyService(settings=build_settings(model_path))
    video_service = VideoSnapshotService(service)
    ground_truth = load_ground_truth(ground_truth_path)
    frame_data = load_frame_data(service, video_service, ground_truth)
    summary_rows = []
    mismatch_rows = []

    for confidence in confidence_values:
        print(f"Running detections for confidence={confidence:.2f}...")
        detections_by_frame = detect_for_confidence(service, frame_data, confidence)
        for slot_threshold in slot_values:
            for box_threshold in box_values:
                summary, mismatches = evaluate_thresholds(
                    service,
                    frame_data,
                    detections_by_frame,
                    confidence=confidence,
                    slot_threshold=slot_threshold,
                    box_threshold=box_threshold,
                )
                summary["model"] = model_name
                summary_rows.append(summary)
                mismatch_rows.extend(mismatches)

    return sorted(summary_rows, key=rank_key, reverse=True), mismatch_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tune ParkViewRT YOLO and slot-overlap thresholds."
    )
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--confidence-values",
        default="0.10,0.15,0.20,0.25,0.30,0.35,0.40",
    )
    parser.add_argument(
        "--slot-values",
        default="0.15,0.20,0.25,0.30,0.35,0.40",
    )
    parser.add_argument(
        "--box-values",
        default="0.10,0.15,0.20,0.25,0.30",
    )
    args = parser.parse_args()

    summary_rows, mismatch_rows = run_tuning(
        model_name=args.model,
        confidence_values=parse_grid(args.confidence_values),
        slot_values=parse_grid(args.slot_values),
        box_values=parse_grid(args.box_values),
        ground_truth_path=args.ground_truth,
    )

    write_csv(args.output_dir / "threshold_tuning_summary.csv", summary_rows)
    if mismatch_rows:
        write_csv(args.output_dir / "threshold_tuning_mismatches.csv", mismatch_rows)

    best = summary_rows[0]
    print("Best threshold set:")
    print(
        f"confidence={best['confidence_threshold']:.2f}, "
        f"slot={best['slot_overlap_threshold']:.2f}, "
        f"box={best['box_overlap_threshold']:.2f}, "
        f"accuracy={best['accuracy']:.2%}, "
        f"correct={best['correct_slots']}/{best['slots']}"
    )
    print(f"Saved: {args.output_dir / 'threshold_tuning_summary.csv'}")
    if mismatch_rows:
        print(f"Saved: {args.output_dir / 'threshold_tuning_mismatches.csv'}")


if __name__ == "__main__":
    main()
