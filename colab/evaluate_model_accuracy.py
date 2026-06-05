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
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "colab" / "outputs"
DEFAULT_GROUND_TRUTH_PATH = (
    PROJECT_ROOT / "colab" / "ground_truth" / "slot_status_ground_truth.csv"
)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.settings import AppSettings, DetectionSettings, get_settings  # noqa: E402
from app.services.occupancy import ParkingOccupancyService  # noqa: E402
from app.services.video_snapshot import VideoSnapshotService  # noqa: E402


DEFAULT_MODELS = [
    "yolo11n.pt",
    "yolo26n.pt",
    "yolo12n.pt",
    "yolov8n.pt",
]
VALID_STATUSES = {"occupied", "available", "occluded"}


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


def analyze_frame(
    service: ParkingOccupancyService,
    video_service: VideoSnapshotService,
    location_id: str,
    variant: str,
    frame_index: int,
) -> tuple[dict, float]:
    video_path = video_service._find_video_path(location_id, variant)
    frame, actual_frame_index = video_service._read_frame(video_path, frame_index)
    if actual_frame_index != frame_index:
        raise ValueError(
            f"Requested frame {frame_index}, but video returned frame {actual_frame_index}"
        )

    start_time = time.perf_counter()
    analysis = service._analyze_location(
        location_id,
        image_source=frame,
        variant=variant,
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return analysis, elapsed_ms


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


def summarize_model(
    model_name: str,
    frame_rows: list[dict],
    slot_rows: list[dict],
) -> dict:
    total_slots = len(slot_rows)
    correct_slots = sum(row["correct"] == "true" for row in slot_rows)
    confusion = Counter(
        (row["expected_status"], row["predicted_status"]) for row in slot_rows
    )
    occupied = precision_recall_f1(confusion, "occupied")
    available = precision_recall_f1(confusion, "available")
    occluded = precision_recall_f1(confusion, "occluded")

    return {
        "model": model_name,
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
        "inference_ms_mean": mean(float(row["inference_ms"]) for row in frame_rows),
        "detections_mean": mean(int(row["detections"]) for row in frame_rows),
    }


def run_accuracy(
    model_names: list[str],
    ground_truth_path: Path,
) -> tuple[list[dict], list[dict], list[dict]]:
    ground_truth = load_ground_truth(ground_truth_path)
    summary_rows = []
    all_frame_rows = []
    all_slot_rows = []

    for model_name in model_names:
        model_path = resolve_model_path(model_name)
        service = ParkingOccupancyService(settings=build_settings(model_path))
        video_service = VideoSnapshotService(service)
        model_frame_rows = []
        model_slot_rows = []
        print(f"Evaluating accuracy for {model_name}...")

        for frame_id, expected_rows in ground_truth.items():
            first_row = expected_rows[0]
            location_id = first_row["location_id"]
            variant = first_row["variant"]
            frame_index = int(first_row["frame_index"])
            analysis, elapsed_ms = analyze_frame(
                service,
                video_service=video_service,
                location_id=location_id,
                variant=variant,
                frame_index=frame_index,
            )
            prediction_lookup = {
                slot["slot_id"]: slot for slot in analysis["slots"]
            }

            frame_correct = 0
            for expected_row in expected_rows:
                slot_id = expected_row["slot_id"]
                predicted_status = prediction_lookup[slot_id]["status"]
                expected_status = expected_row["expected_status"]
                correct = predicted_status == expected_status
                if correct:
                    frame_correct += 1
                model_slot_rows.append(
                    {
                        "model": model_name,
                        "frame_id": frame_id,
                        "location_id": location_id,
                        "variant": variant,
                        "frame_index": frame_index,
                        "slot_id": slot_id,
                        "expected_status": expected_status,
                        "predicted_status": predicted_status,
                        "correct": str(correct).lower(),
                        "occupied_reason": prediction_lookup[slot_id][
                            "occupied_reason"
                        ],
                        "overlap_ratio": prediction_lookup[slot_id][
                            "overlap_ratio"
                        ],
                        "box_overlap_ratio": prediction_lookup[slot_id][
                            "box_overlap_ratio"
                        ],
                    }
                )

            model_frame_rows.append(
                {
                    "model": model_name,
                    "frame_id": frame_id,
                    "location_id": location_id,
                    "variant": variant,
                    "frame_index": frame_index,
                    "slots": len(expected_rows),
                    "correct_slots": frame_correct,
                    "accuracy": frame_correct / len(expected_rows),
                    "detections": len(analysis["detections"]),
                    "inference_ms": elapsed_ms,
                }
            )

        summary_rows.append(
            summarize_model(model_name, model_frame_rows, model_slot_rows)
        )
        all_frame_rows.extend(model_frame_rows)
        all_slot_rows.extend(model_slot_rows)

    return summary_rows, all_frame_rows, all_slot_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate YOLO model slot-status accuracy on verified frames."
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary_rows, frame_rows, slot_rows = run_accuracy(
        model_names=args.models,
        ground_truth_path=args.ground_truth,
    )

    write_csv(args.output_dir / "model_accuracy_summary.csv", summary_rows)
    write_csv(args.output_dir / "model_accuracy_frames.csv", frame_rows)
    write_csv(args.output_dir / "model_accuracy_slots.csv", slot_rows)

    print(f"Saved: {args.output_dir / 'model_accuracy_summary.csv'}")
    print(f"Saved: {args.output_dir / 'model_accuracy_frames.csv'}")
    print(f"Saved: {args.output_dir / 'model_accuracy_slots.csv'}")


if __name__ == "__main__":
    main()
