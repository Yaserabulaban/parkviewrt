import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "colab" / "outputs" / "model_comparison_summary.csv"
DEFAULT_SLOTS_PATH = PROJECT_ROOT / "colab" / "outputs" / "model_comparison_slots.csv"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / "model_evaluation.md"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV file: {path}")

    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def to_float(value: str) -> float:
    return float(value)


def to_int(value: str) -> int:
    return int(float(value))


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *row_lines])


def summarize_models(summary_rows: list[dict]) -> list[dict]:
    grouped_rows = defaultdict(list)
    for row in summary_rows:
        grouped_rows[row["model"]].append(row)

    summaries = []
    for model_name, rows in grouped_rows.items():
        summaries.append(
            {
                "model": model_name,
                "variants": len(rows),
                "total_detections": sum(to_int(row["detections"]) for row in rows),
                "occupied_count": sum(to_int(row["occupied_count"]) for row in rows),
                "available_count": sum(to_int(row["available_count"]) for row in rows),
                "occluded_count": sum(to_int(row["occluded_count"]) for row in rows),
                "average_inference_ms": mean(
                    to_float(row["inference_ms_mean"]) for row in rows
                ),
            }
        )

    return sorted(summaries, key=lambda row: row["average_inference_ms"])


def collect_selected_notes(summary_rows: list[dict], selected_model: str) -> list[list[str]]:
    notes = []
    for row in summary_rows:
        if row["model"] != selected_model:
            continue
        notes.append(
            [
                row["location_id"].upper(),
                row["variant"],
                row["total_slots"],
                row["detections"],
                row["occupied_count"],
                row["available_count"],
                row["occluded_count"],
                row["empty_slots"] or "-",
                row["occluded_slots"] or "-",
            ]
        )
    return notes


def build_report(
    summary_rows: list[dict],
    slot_rows: list[dict],
    selected_model: str,
) -> str:
    del slot_rows

    model_summaries = summarize_models(summary_rows)
    selected_summary = next(
        (row for row in model_summaries if row["model"] == selected_model),
        None,
    )
    if selected_summary is None:
        raise ValueError(f"Selected model was not found in summary CSV: {selected_model}")

    model_summary_table = format_table(
        [
            "Model",
            "Variants",
            "Total Detections",
            "Occupied Slots",
            "Available Slots",
            "Occluded Slots",
            "Avg Pipeline Time (ms)",
        ],
        [
            [
                row["model"],
                str(row["variants"]),
                str(row["total_detections"]),
                str(row["occupied_count"]),
                str(row["available_count"]),
                str(row["occluded_count"]),
                f"{row['average_inference_ms']:.2f}",
            ]
            for row in model_summaries
        ],
    )

    location_table = format_table(
        [
            "Model",
            "Location",
            "Variant",
            "Slots",
            "Detections",
            "Occupied",
            "Available",
            "Occluded",
            "Avg Pipeline Time (ms)",
        ],
        [
            [
                row["model"],
                row["location_id"].upper(),
                row["variant"],
                row["total_slots"],
                row["detections"],
                row["occupied_count"],
                row["available_count"],
                row["occluded_count"],
                f"{to_float(row['inference_ms_mean']):.2f}",
            ]
            for row in summary_rows
        ],
    )

    selected_detail_table = format_table(
        [
            "Location",
            "Variant",
            "Slots",
            "Detections",
            "Occupied",
            "Available",
            "Occluded",
            "Available Slot IDs",
            "Occluded Slot IDs",
        ],
        collect_selected_notes(summary_rows, selected_model),
    )

    return f"""# ParkViewRT YOLO Model Evaluation

This document summarizes the current pretrained YOLO comparison for ParkViewRT.
The run compares the production model against current/latest suitable Ultralytics
nano detection checkpoints using the same backend thresholds and the current
runtime slot JSON files.

## Evaluation Setup

```text
Input images:
- backend/app/data/images/fci_day.png
- backend/app/data/images/fci_night.png
- backend/app/data/images/faie_day.png
- backend/app/data/images/faie_night.png

Runtime slot files:
- backend/app/data/slots/fci_day_slots.json
- backend/app/data/slots/fci_night_slots.json
- backend/app/data/slots/faie_day_slots.json
- backend/app/data/slots/faie_night_slots.json

Detection classes: car, truck
Confidence threshold: 0.20
Image size: 1600
Slot overlap threshold: 0.25
Box overlap threshold: 0.20
Runs per model/location/variant: 3 measured runs after 1 warmup run
```

## Compared Models

```text
yolo11n.pt  current production baseline
yolo26n.pt  latest Ultralytics production family, nano checkpoint
yolo12n.pt  newer attention-centric/community checkpoint, nano scale
yolov8n.pt  previous stable nano baseline for regression comparison
```

Ultralytics documents YOLO26 as the latest edge-oriented family, and documents
YOLO12 as a community/research line with production caveats. Because ParkViewRT
needs near-real-time dashboard inference, this comparison uses nano checkpoints
only instead of mixing nano/small/medium sizes.

## Important Limitation

These results are measured backend behavior, not final accuracy. The current
four reference images do not include manually verified ground-truth status for
every monitored slot. Therefore, the tables below should be used to justify a
practical model choice, then revisited once a labelled validation set of video
frames is prepared.

## Selected Model

```text
{selected_model}
```

`{selected_model}` remains the selected backend model for now.

Reason:

```text
It was the fastest model in the current run, matched YOLO26 on total detections,
detected more occupied FAIE day slots than YOLO26, and avoided the large latency
increase seen with YOLO12. YOLO26 remains the first model to retest when a
ground-truth validation set is available, but this run does not show enough
benefit to replace the stable current model.
```

## Model Summary

{model_summary_table}

## Variant Results

{location_table}

## Selected Model Variant Details

{selected_detail_table}

## Generated Artifacts

```text
colab/outputs/model_comparison_summary.csv
colab/outputs/model_comparison_slots.csv
colab/outputs/debug_images/
```

The `colab/outputs/` folder is ignored by Git because it contains generated
experiment artifacts.

## Sources For Model Choice

- Ultralytics YOLO11 documentation: https://docs.ultralytics.com/models/yolo11/
- Ultralytics YOLO12 documentation: https://docs.ultralytics.com/models/yolo12/
- Ultralytics YOLO26 documentation: https://docs.ultralytics.com/models/yolo26/
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ParkViewRT model evaluation report.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--slots", type=Path, default=DEFAULT_SLOTS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--selected-model", default="yolo11n.pt")
    args = parser.parse_args()

    summary_rows = read_csv(args.summary)
    slot_rows = read_csv(args.slots)
    report = build_report(summary_rows, slot_rows, args.selected_model)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Saved report: {args.output}")


if __name__ == "__main__":
    main()
