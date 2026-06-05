import argparse
import csv
import sys
import time
from pathlib import Path
from statistics import mean

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MODEL_DIR = BACKEND_DIR / "app" / "models"
OUTPUT_DIR = PROJECT_ROOT / "colab" / "outputs"
DEBUG_DIR = OUTPUT_DIR / "debug_images"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.settings import AppSettings, DetectionSettings, get_settings  # noqa: E402
from app.services.occupancy import ParkingOccupancyService  # noqa: E402


DEFAULT_MODELS = [
    "yolo11n.pt",
    "yolo26n.pt",
    "yolo12n.pt",
    "yolov8n.pt",
]
DATASETS = [
    ("fci", "day"),
    ("fci", "night"),
    ("faie", "day"),
    ("faie", "night"),
]


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


def summarize_slots(slots: list[dict]) -> dict:
    occupied_count = sum(slot["status"] == "occupied" for slot in slots)
    occluded_count = sum(slot["status"] == "occluded" for slot in slots)
    available_count = len(slots) - occupied_count - occluded_count
    return {
        "occupied_count": occupied_count,
        "available_count": available_count,
        "occluded_count": occluded_count,
        "empty_slots": " ".join(
            slot["slot_id"] for slot in slots if slot["status"] == "available"
        ),
        "occluded_slots": " ".join(
            slot["slot_id"] for slot in slots if slot["status"] == "occluded"
        ),
    }


def write_debug_image(
    service: ParkingOccupancyService,
    analysis: dict,
    output_path: Path,
) -> None:
    image = cv2.imread(str(analysis["image_path"]))
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {analysis['image_path']}")

    slot_lookup = {slot["slot_id"]: slot for slot in analysis["slots"]}
    service._draw_slots(image, analysis["slot_data"]["slots"], slot_lookup)
    service._draw_detections(image, analysis["detections"])
    service._draw_summary(image, analysis)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def run_dataset(
    service: ParkingOccupancyService,
    location_id: str,
    variant: str,
    runs: int,
    warmup_runs: int,
) -> tuple[dict, list[float]]:
    analysis = None

    for _ in range(warmup_runs):
        analysis = service._analyze_location(location_id, variant=variant)

    elapsed_runs = []
    for _ in range(runs):
        start_time = time.perf_counter()
        analysis = service._analyze_location(location_id, variant=variant)
        elapsed_runs.append((time.perf_counter() - start_time) * 1000)

    if analysis is None:
        raise RuntimeError("No analysis was produced")
    return analysis, elapsed_runs


def run_comparison(
    model_names: list[str],
    runs: int,
    warmup_runs: int,
    output_dir: Path,
    write_debug: bool,
) -> tuple[list[dict], list[dict]]:
    summary_rows = []
    slot_rows = []

    for model_name in model_names:
        model_path = resolve_model_path(model_name)
        service = ParkingOccupancyService(settings=build_settings(model_path))
        print(f"Evaluating {model_name}...")

        for location_id, variant in DATASETS:
            analysis, elapsed_runs = run_dataset(
                service,
                location_id=location_id,
                variant=variant,
                runs=runs,
                warmup_runs=warmup_runs,
            )
            slot_summary = summarize_slots(analysis["slots"])
            image_path = analysis["image_path"]
            slot_path = PROJECT_ROOT / "backend" / "app" / "data" / "slots" / (
                f"{location_id}_{variant}_slots.json"
            )

            summary_rows.append(
                {
                    "model": model_name,
                    "model_path": str(model_path.relative_to(PROJECT_ROOT)),
                    "location_id": location_id,
                    "variant": variant,
                    "image_path": str(image_path.relative_to(PROJECT_ROOT)),
                    "slot_file": str(slot_path.relative_to(PROJECT_ROOT)),
                    "total_slots": len(analysis["slots"]),
                    "detections": len(analysis["detections"]),
                    "occupied_count": slot_summary["occupied_count"],
                    "available_count": slot_summary["available_count"],
                    "occluded_count": slot_summary["occluded_count"],
                    "inference_ms_mean": mean(elapsed_runs),
                    "inference_ms_min": min(elapsed_runs),
                    "inference_ms_max": max(elapsed_runs),
                    "confidence_threshold": analysis["confidence_threshold"],
                    "image_size": analysis["image_size"],
                    "slot_overlap_threshold": analysis["overlap_threshold"],
                    "box_overlap_threshold": analysis["box_overlap_threshold"],
                    "empty_slots": slot_summary["empty_slots"],
                    "occluded_slots": slot_summary["occluded_slots"],
                }
            )

            for slot in analysis["slots"]:
                slot_rows.append(
                    {
                        "model": model_name,
                        "location_id": location_id,
                        "variant": variant,
                        "slot_id": slot["slot_id"],
                        "status": slot["status"],
                        "occupied": slot["occupied"],
                        "overlap_ratio": slot["overlap_ratio"],
                        "box_overlap_ratio": slot["box_overlap_ratio"],
                        "detection_center_in_slot": slot["detection_center_in_slot"],
                        "slot_centroid_in_detection": slot["slot_centroid_in_detection"],
                        "occupied_reason": slot["occupied_reason"],
                    }
                )

            if write_debug:
                safe_model_name = model_name.replace(".pt", "").replace("/", "_")
                debug_path = (
                    output_dir
                    / "debug_images"
                    / f"debug_{safe_model_name}_{location_id}_{variant}.jpg"
                )
                write_debug_image(service, analysis, debug_path)

    return summary_rows, slot_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")

    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare pretrained YOLO models on current ParkViewRT images."
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--no-debug-images", action="store_true")
    args = parser.parse_args()

    summary_rows, slot_rows = run_comparison(
        model_names=args.models,
        runs=args.runs,
        warmup_runs=args.warmup_runs,
        output_dir=args.output_dir,
        write_debug=not args.no_debug_images,
    )

    summary_path = args.output_dir / "model_comparison_summary.csv"
    slots_path = args.output_dir / "model_comparison_slots.csv"
    write_csv(summary_path, summary_rows)
    write_csv(slots_path, slot_rows)

    print(f"Saved: {summary_path}")
    print(f"Saved: {slots_path}")
    if not args.no_debug_images:
        print(f"Saved debug images under: {args.output_dir / 'debug_images'}")


if __name__ == "__main__":
    main()
