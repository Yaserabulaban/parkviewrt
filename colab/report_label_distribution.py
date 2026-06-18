import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GROUND_TRUTH = (
    PROJECT_ROOT / "colab" / "ground_truth" / "slot_status_ground_truth.csv"
)
DEFAULT_OUTPUT_CSV = (
    PROJECT_ROOT
    / "colab"
    / "outputs"
    / "validation"
    / "label_distribution.csv"
)
DEFAULT_OUTPUT_MD = (
    PROJECT_ROOT
    / "colab"
    / "outputs"
    / "validation"
    / "label_distribution.md"
)
STATUSES = ("available", "occupied", "occluded")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing ground-truth CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def count_rows(rows: list[dict]) -> Counter:
    return Counter((row.get("status") or row.get("expected_status")).lower() for row in rows)


def distribution_rows(rows: list[dict]) -> list[dict]:
    groups = [("overall", "", "", "", rows)]
    by_variant = defaultdict(list)
    by_frame = defaultdict(list)
    for row in rows:
        variant_key = (row["location_id"], row["variant"])
        frame_key = (
            row["location_id"],
            row["variant"],
            row["frame_index"],
        )
        by_variant[variant_key].append(row)
        by_frame[frame_key].append(row)

    groups.extend(
        ("variant", location_id, variant, "", group_rows)
        for (location_id, variant), group_rows in sorted(by_variant.items())
    )
    groups.extend(
        ("frame", location_id, variant, frame_index, group_rows)
        for (location_id, variant, frame_index), group_rows in sorted(
            by_frame.items(),
            key=lambda item: (item[0][0], item[0][1], int(item[0][2])),
        )
    )

    output = []
    for scope, location_id, variant, frame_index, group_rows in groups:
        counts = count_rows(group_rows)
        total = len(group_rows)
        for status in STATUSES:
            count = counts[status]
            output.append(
                {
                    "scope": scope,
                    "location_id": location_id,
                    "variant": variant,
                    "frame_index": frame_index,
                    "status": status,
                    "count": count,
                    "percentage": f"{count / total * 100:.2f}" if total else "0.00",
                    "total_labels": total,
                }
            )
    return output


def markdown_report(rows: list[dict]) -> str:
    overall = count_rows(rows)
    total = len(rows)
    verification = Counter(row.get("verification_status", "unknown") for row in rows)
    by_variant = defaultdict(list)
    for row in rows:
        by_variant[(row["location_id"], row["variant"])].append(row)

    overall_lines = [
        "| Status | Count | Percentage |",
        "| --- | ---: | ---: |",
    ]
    for status in STATUSES:
        count = overall[status]
        overall_lines.append(
            f"| {status} | {count} | {count / total * 100:.2f}% |"
        )

    variant_lines = [
        "| Location | Variant | Labels | Available | Occupied | Occluded |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for (location_id, variant), group_rows in sorted(by_variant.items()):
        counts = count_rows(group_rows)
        group_total = len(group_rows)
        values = [
            f"{counts[status]} ({counts[status] / group_total * 100:.2f}%)"
            for status in STATUSES
        ]
        variant_lines.append(
            f"| {location_id.upper()} | {variant} | {group_total} | "
            f"{values[0]} | {values[1]} | {values[2]} |"
        )

    dominant_status, dominant_count = overall.most_common(1)[0]
    balance_note = (
        f"The largest class is `{dominant_status}` with "
        f"{dominant_count / total * 100:.2f}% of labels. "
        "The distribution reflects the observed parking videos and should not be "
        "described as perfectly balanced unless the reviewed counts change."
    )

    return f"""# Validation Label Distribution

## Validation Size

```text
Frames: {len({row['frame_id'] for row in rows})}
Slot labels: {total}
Reviewed labels: {verification['verified']}
Preliminary labels: {verification['preliminary']}
```

Preliminary rows are assisted labels and must be manually checked before they
are used for the official model comparison or threshold tuning.

## Overall Status Distribution

{chr(10).join(overall_lines)}

## Status Distribution By Variant

{chr(10).join(variant_lines)}

## Balance Interpretation

{balance_note}

The detailed CSV also contains per-frame counts and percentages:

```text
colab/outputs/validation/label_distribution.csv
```
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report ParkViewRT ground-truth status distributions."
    )
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    args = parser.parse_args()

    rows = read_csv(args.ground_truth)
    output_rows = distribution_rows(rows)
    write_csv(args.output_csv, output_rows)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown_report(rows), encoding="utf-8")
    print(f"Saved: {args.output_csv}")
    print(f"Saved: {args.output_md}")


if __name__ == "__main__":
    main()
