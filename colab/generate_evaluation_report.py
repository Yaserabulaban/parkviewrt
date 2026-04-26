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


def summarize_models(summary_rows: list[dict], slot_rows: list[dict]) -> list[dict]:
    grouped_summary = defaultdict(list)
    grouped_slots = defaultdict(list)

    for row in summary_rows:
        grouped_summary[row["model"]].append(row)

    for row in slot_rows:
        grouped_slots[row["model"]].append(row)

    model_summaries = []
    for model_name in sorted(grouped_summary):
        rows = grouped_summary[model_name]
        slots = grouped_slots[model_name]
        model_summaries.append(
            {
                "model": model_name,
                "locations": len(rows),
                "total_detections": sum(to_int(row["detections"]) for row in rows),
                "average_accuracy": mean(to_float(row["slot_accuracy"]) for row in rows),
                "average_inference_ms": mean(to_float(row["inference_ms"]) for row in rows),
                "minimum_slot_overlap": min(to_float(row["slot_overlap"]) for row in slots),
                "minimum_box_overlap": min(to_float(row["box_overlap"]) for row in slots),
            }
        )

    return sorted(
        model_summaries,
        key=lambda row: (
            -row["average_accuracy"],
            row["average_inference_ms"],
            -row["minimum_slot_overlap"],
        ),
    )


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, separator, *row_lines])


def build_report(
    summary_rows: list[dict],
    slot_rows: list[dict],
    selected_model: str,
) -> str:
    model_summaries = summarize_models(summary_rows, slot_rows)
    model_summaries = sorted(
        model_summaries,
        key=lambda row: (row["model"] != selected_model, row["model"]),
    )
    selected_summary = next(
        (row for row in model_summaries if row["model"] == selected_model),
        None,
    )
    if selected_summary is None:
        raise ValueError(f"Selected model was not found in summary CSV: {selected_model}")

    model_table = format_table(
        [
            "Model",
            "Locations",
            "Total Detections",
            "Avg Slot Accuracy",
            "Avg Inference (ms)",
            "Min Slot Overlap",
            "Min Box Overlap",
        ],
        [
            [
                row["model"],
                str(row["locations"]),
                str(row["total_detections"]),
                f"{row['average_accuracy']:.2%}",
                f"{row['average_inference_ms']:.2f}",
                f"{row['minimum_slot_overlap']:.2%}",
                f"{row['minimum_box_overlap']:.2%}",
            ]
            for row in model_summaries
        ],
    )

    location_table = format_table(
        [
            "Model",
            "Location",
            "Detections",
            "Occupied",
            "Available",
            "Slot Accuracy",
            "Inference (ms)",
        ],
        [
            [
                row["model"],
                row["location_id"].upper(),
                row["detections"],
                row["occupied_count"],
                row["available_count"],
                f"{to_float(row['slot_accuracy']):.2%}",
                f"{to_float(row['inference_ms']):.2f}",
            ]
            for row in summary_rows
        ],
    )

    selected_slot_rows = [
        row for row in slot_rows if row["model"] == selected_model
    ]
    selected_slot_table = format_table(
        ["Location", "Slot", "Occupied", "Slot Overlap", "Box Overlap"],
        [
            [
                row["location_id"].upper(),
                row["slot_id"],
                row["occupied"],
                f"{to_float(row['slot_overlap']):.2%}",
                f"{to_float(row['box_overlap']):.2%}",
            ]
            for row in selected_slot_rows
        ],
    )

    return f"""# ParkViewRT Model Evaluation

This document summarizes the pretrained YOLO model comparison for the current FCI and FAIE static parking images.

## Evaluation Setup

```text
Input images: backend/app/data/images/fci.jpeg, backend/app/data/images/faie.jpeg
Slot labels: backend/app/data/slots/fci_slots.json, backend/app/data/slots/faie_slots.json
Detection class: car only
Confidence threshold: 0.20
Image size: 1600
Slot overlap threshold: 0.30
Box overlap threshold: 0.20
```

The current labelled static images contain the eight selected slots for each location, and those selected slots are treated as occupied for this comparison.

## Selected Model

```text
{selected_model}
```

`{selected_model}` remains the production backend model for now. The comparison confirms that it correctly marks all labelled static slots as occupied, and the debug images were visually reliable for the current MMU parking images.

All compared models reached full slot accuracy on this small static-image set. Because the current test set is limited, the production choice also considers visual debug quality, existing backend compatibility, and the need to retest once real videos are available.

This decision should be revisited after real FCI and FAIE videos are collected, because video frames may include motion blur, lighting changes, different occupancy levels, and more occlusion.

## Model Summary

{model_table}

## Location Results

{location_table}

## Selected Model Slot Details

{selected_slot_table}

## Generated Artifacts

The local evaluation run also creates:

```text
colab/outputs/model_comparison_summary.csv
colab/outputs/model_comparison_slots.csv
colab/outputs/debug_images/
```

The `colab/outputs/` folder is ignored by Git because it contains generated experiment artifacts.
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
