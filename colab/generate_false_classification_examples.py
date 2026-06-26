import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DEFAULT_RESULTS = PROJECT_ROOT / "colab" / "outputs" / "model_accuracy_slots.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "colab" / "outputs" / "false_classification_examples"
DEFAULT_REPORT_ASSET_DIR = PROJECT_ROOT / "docs" / "report_assets"
SLOTS_DIR = BACKEND_DIR / "app" / "data" / "slots"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.occupancy import ParkingOccupancyService  # noqa: E402
from app.services.video_snapshot import VideoSnapshotService  # noqa: E402


MODELS = ("yolo12n.pt", "yolo26n.pt", "yolov8n.pt")
MODEL_LABELS = {
    "yolo12n.pt": "YOLO12n",
    "yolo26n.pt": "YOLO26n",
    "yolov8n.pt": "YOLOv8n",
}
PREDICTED_COLORS = {
    "available": (0, 175, 70),
    "occupied": (40, 40, 230),
    "occluded": (0, 170, 255),
}
# Pick clear examples where possible. FAIE crops are less crowded in print,
# but each model still uses a real mismatch from the evaluation CSV.
PREFERRED_EXAMPLES = {
    "yolo12n.pt": (
        ("fci", "day"),
        ("fci", "night"),
        ("faie", "day"),
        ("faie", "night"),
    ),
    "yolo26n.pt": (
        ("faie", "day"),
        ("fci", "night"),
        ("fci", "day"),
        ("faie", "night"),
    ),
    "yolov8n.pt": (
        ("faie", "day"),
        ("fci", "night"),
        ("fci", "day"),
        ("faie", "night"),
    ),
}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mismatch_priority(row: dict) -> tuple:
    # False available is the most important report example because it can show
    # a genuinely occupied or occluded slot as free.
    predicted = row["predicted_status"]
    expected = row["expected_status"]
    return (
        0 if predicted == "available" and expected != "available" else 1,
        0 if predicted == "occupied" and expected != "occupied" else 1,
        int(row["frame_index"]),
        row["slot_id"],
    )


def select_model_examples(rows: list[dict]) -> dict[str, dict]:
    mismatches_by_model_variant: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        if row["model"] not in MODELS or row["correct"] != "false":
            continue
        key = (row["model"], row["location_id"], row["variant"])
        current = mismatches_by_model_variant.get(key)
        if current is None or mismatch_priority(row) < mismatch_priority(current):
            mismatches_by_model_variant[key] = row

    selected = {}
    for model_name in MODELS:
        for location_id, variant in PREFERRED_EXAMPLES[model_name]:
            key = (model_name, location_id, variant)
            if key in mismatches_by_model_variant:
                selected[model_name] = mismatches_by_model_variant[key]
                break
        if model_name not in selected:
            model_rows = [
                row for key, row in mismatches_by_model_variant.items() if key[0] == model_name
            ]
            if model_rows:
                selected[model_name] = min(model_rows, key=mismatch_priority)
    return selected


def load_slot_points(location_id: str, variant: str, slot_id: str) -> np.ndarray:
    path = SLOTS_DIR / f"{location_id}_{variant}_slots.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for slot in data["slots"]:
        if slot["slot_id"] == slot_id:
            return np.asarray(slot["points"], dtype=np.int32)
    raise KeyError(f"{slot_id} was not found in {path}")


def crop_slot(frame: np.ndarray, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y, width, height = cv2.boundingRect(points)
    margin_x = max(140, width * 3)
    margin_y = max(120, height * 3)
    left = max(0, x - margin_x)
    top = max(0, y - margin_y)
    right = min(frame.shape[1], x + width + margin_x)
    bottom = min(frame.shape[0], y + height + margin_y)
    crop = frame[top:bottom, left:right].copy()
    adjusted = points - np.asarray([left, top], dtype=np.int32)
    return crop, adjusted


def fit_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    scale = min(width / image.shape[1], height / image.shape[0])
    resized = cv2.resize(
        image,
        (
            max(1, int(image.shape[1] * scale)),
            max(1, int(image.shape[0] * scale)),
        ),
        interpolation=cv2.INTER_AREA,
    )
    x = (width - resized.shape[1]) // 2
    y = (height - resized.shape[0]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    return canvas


def draw_multiline(
    image: np.ndarray,
    lines: list[str],
    origin: tuple[int, int],
    color: tuple[int, int, int],
    font_scale: float,
    thickness: int,
    line_height: int,
) -> None:
    x, y = origin
    for index, line in enumerate(lines):
        cv2.putText(
            image,
            line,
            (x, y + index * line_height),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )


def create_example_figure(
    video_service: VideoSnapshotService,
    row: dict,
    output_path: Path,
    width: int = 1600,
    height: int = 1050,
) -> dict:
    video_path = video_service._find_video_path(row["location_id"], row["variant"])
    frame, _ = video_service._read_frame(video_path, int(row["frame_index"]))
    points = load_slot_points(row["location_id"], row["variant"], row["slot_id"])
    crop, adjusted_points = crop_slot(frame, points)

    predicted_color = PREDICTED_COLORS[row["predicted_status"]]
    overlay = crop.copy()
    cv2.fillPoly(overlay, [adjusted_points], predicted_color)
    crop = cv2.addWeighted(overlay, 0.25, crop, 0.75, 0)
    cv2.polylines(crop, [adjusted_points], True, predicted_color, 7, cv2.LINE_AA)

    image_height = height - 160
    fitted = fit_image(crop, width - 24, image_height - 12)
    figure = np.full((height, width, 3), 250, dtype=np.uint8)
    figure[12 : 12 + fitted.shape[0], 12 : 12 + fitted.shape[1]] = fitted

    cv2.rectangle(figure, (0, height - 155), (width - 1, height - 1), (32, 36, 42), -1)
    title = f"{MODEL_LABELS[row['model']]} False Classification Example"
    details = [
        f"{row['location_id'].upper()} {row['variant'].title()} | Slot {row['slot_id']} | Frame {row['frame_index']}",
        f"Expected: {row['expected_status'].title()} | Predicted: {row['predicted_status'].title()}",
    ]
    draw_multiline(figure, [title], (28, height - 112), (255, 255, 255), 0.9, 2, 34)
    draw_multiline(figure, details, (28, height - 72), (230, 235, 240), 0.68, 2, 30)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), figure)
    return {
        "model": row["model"],
        "location_id": row["location_id"],
        "variant": row["variant"],
        "frame_index": row["frame_index"],
        "slot_id": row["slot_id"],
        "expected_status": row["expected_status"],
        "predicted_status": row["predicted_status"],
        "output_path": str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate one standalone false-classification example per model."
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-asset-dir", type=Path, default=DEFAULT_REPORT_ASSET_DIR)
    args = parser.parse_args()

    rows = read_csv(args.results)
    selected_examples = select_model_examples(rows)
    video_service = VideoSnapshotService(ParkingOccupancyService())
    summary_rows = []

    for model_name in MODELS:
        if model_name not in selected_examples:
            print(f"No false-classification example found for {model_name}")
            continue
        output_path = args.report_asset_dir / (
            f"{Path(model_name).stem}_false_classification_example.png"
        )
        summary_rows.append(
            create_example_figure(video_service, selected_examples[model_name], output_path)
        )
        print(f"Saved: {output_path}")

    if not summary_rows:
        raise ValueError("No false-classification examples were found.")
    write_csv(args.output_dir / "false_classification_examples.csv", summary_rows)
    print(f"Saved: {args.output_dir / 'false_classification_examples.csv'}")


if __name__ == "__main__":
    main()
