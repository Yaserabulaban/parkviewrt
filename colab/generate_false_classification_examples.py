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
DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT / "colab" / "outputs" / "false_classification_examples"
)
SLOTS_DIR = BACKEND_DIR / "app" / "data" / "slots"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.occupancy import ParkingOccupancyService  # noqa: E402
from app.services.video_snapshot import VideoSnapshotService  # noqa: E402


MODELS = ("yolo12n.pt", "yolo26n.pt", "yolov8n.pt")
VARIANTS = (
    ("fci", "day"),
    ("fci", "night"),
    ("faie", "day"),
    ("faie", "night"),
)
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
    # False available is the most important example because it can show a
    # genuinely occupied or occluded slot as free.
    predicted = row["predicted_status"]
    expected = row["expected_status"]
    return (
        0 if predicted == "available" and expected != "available" else 1,
        0 if predicted == "occupied" and expected != "occupied" else 1,
        int(row["frame_index"]),
        row["slot_id"],
    )


def select_examples(rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    grouped = {}
    for row in rows:
        if row["model"] not in MODELS or row["correct"] != "false":
            continue
        key = (row["model"], row["location_id"], row["variant"])
        current = grouped.get(key)
        if current is None or mismatch_priority(row) < mismatch_priority(current):
            grouped[key] = row
    return grouped


def load_slot_points(location_id: str, variant: str, slot_id: str) -> np.ndarray:
    path = SLOTS_DIR / f"{location_id}_{variant}_slots.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for slot in data["slots"]:
        if slot["slot_id"] == slot_id:
            return np.asarray(slot["points"], dtype=np.int32)
    raise KeyError(f"{slot_id} was not found in {path}")


def crop_slot(frame: np.ndarray, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y, width, height = cv2.boundingRect(points)
    margin_x = max(100, width * 2)
    margin_y = max(80, height * 2)
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
    font_scale: float = 0.75,
    thickness: int = 2,
    line_height: int = 34,
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


def create_mismatch_panel(
    video_service: VideoSnapshotService,
    row: dict,
    width: int,
    height: int,
) -> np.ndarray:
    video_path = video_service._find_video_path(row["location_id"], row["variant"])
    frame, _ = video_service._read_frame(video_path, int(row["frame_index"]))
    points = load_slot_points(row["location_id"], row["variant"], row["slot_id"])
    crop, adjusted_points = crop_slot(frame, points)

    predicted_color = PREDICTED_COLORS[row["predicted_status"]]
    overlay = crop.copy()
    cv2.fillPoly(overlay, [adjusted_points], predicted_color)
    crop = cv2.addWeighted(overlay, 0.25, crop, 0.75, 0)
    cv2.polylines(crop, [adjusted_points], True, predicted_color, 6, cv2.LINE_AA)

    image_height = height - 155
    fitted = fit_image(crop, width - 24, image_height - 12)
    panel = np.full((height, width, 3), 250, dtype=np.uint8)
    panel[12 : 12 + fitted.shape[0], 12 : 12 + fitted.shape[1]] = fitted

    title = f"{row['location_id'].upper()} {row['variant'].title()}"
    details = [
        f"Slot {row['slot_id']} | Frame {row['frame_index']}",
        f"Expected: {row['expected_status'].title()}",
        f"Predicted: {row['predicted_status'].title()}",
    ]
    cv2.rectangle(
        panel,
        (0, height - 150),
        (width - 1, height - 1),
        (32, 36, 42),
        -1,
    )
    draw_multiline(panel, [title], (22, height - 112), (255, 255, 255), 0.88, 2)
    draw_multiline(panel, details, (22, height - 72), (230, 235, 240), 0.64, 1, 26)
    return panel


def create_no_mismatch_panel(
    location_id: str,
    variant: str,
    width: int,
    height: int,
) -> np.ndarray:
    panel = np.full((height, width, 3), (241, 245, 249), dtype=np.uint8)
    title = f"{location_id.upper()} {variant.title()}"
    cv2.rectangle(panel, (0, 0), (width - 1, height - 1), (148, 163, 184), 3)
    cv2.putText(
        panel,
        title,
        (32, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.05,
        (15, 23, 42),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        "No false classification found",
        (32, height // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.82,
        (22, 101, 52),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        "All verified slot labels were correct.",
        (32, height // 2 + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (71, 85, 105),
        2,
        cv2.LINE_AA,
    )
    return panel


def create_model_sheet(
    model_name: str,
    examples: dict[tuple[str, str, str], dict],
    video_service: VideoSnapshotService,
    output_path: Path,
) -> list[dict]:
    panel_width = 900
    panel_height = 620
    header_height = 130
    sheet = np.full(
        (header_height + panel_height * 2, panel_width * 2, 3),
        248,
        dtype=np.uint8,
    )
    cv2.rectangle(
        sheet,
        (0, 0),
        (sheet.shape[1] - 1, header_height - 1),
        (22, 26, 31),
        -1,
    )
    cv2.putText(
        sheet,
        f"{MODEL_LABELS[model_name]} False Classification Examples",
        (42, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.35,
        (255, 255, 255),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        sheet,
        "One actual mismatch per video variant where a mismatch exists",
        (42, 103),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (205, 213, 222),
        2,
        cv2.LINE_AA,
    )

    summary_rows = []
    for index, (location_id, variant) in enumerate(VARIANTS):
        key = (model_name, location_id, variant)
        row = examples.get(key)
        if row:
            panel = create_mismatch_panel(
                video_service,
                row,
                panel_width,
                panel_height,
            )
            summary_rows.append(
                {
                    "model": model_name,
                    "location_id": location_id,
                    "variant": variant,
                    "has_mismatch": "yes",
                    "frame_index": row["frame_index"],
                    "slot_id": row["slot_id"],
                    "expected_status": row["expected_status"],
                    "predicted_status": row["predicted_status"],
                }
            )
        else:
            panel = create_no_mismatch_panel(
                location_id,
                variant,
                panel_width,
                panel_height,
            )
            summary_rows.append(
                {
                    "model": model_name,
                    "location_id": location_id,
                    "variant": variant,
                    "has_mismatch": "no",
                    "frame_index": "",
                    "slot_id": "",
                    "expected_status": "",
                    "predicted_status": "",
                }
            )

        row_index = index // 2
        column_index = index % 2
        top = header_height + row_index * panel_height
        left = column_index * panel_width
        sheet[top : top + panel_height, left : left + panel_width] = panel

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), sheet)
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate report-ready false-classification example sheets."
    )
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    rows = read_csv(args.results)
    examples = select_examples(rows)
    video_service = VideoSnapshotService(ParkingOccupancyService())
    summary_rows = []

    for model_name in MODELS:
        output_path = args.output_dir / (
            f"{Path(model_name).stem}_false_classification_examples.png"
        )
        summary_rows.extend(
            create_model_sheet(
                model_name,
                examples,
                video_service,
                output_path,
            )
        )
        print(f"Saved: {output_path}")

    write_csv(args.output_dir / "false_classification_examples.csv", summary_rows)
    print(f"Saved: {args.output_dir / 'false_classification_examples.csv'}")


if __name__ == "__main__":
    main()
