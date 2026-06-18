import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GROUND_TRUTH = (
    PROJECT_ROOT / "colab" / "ground_truth" / "slot_status_ground_truth.csv"
)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Mark manually reviewed ground-truth frames as verified. "
            "Run this only after checking the matching debug images and correcting "
            "any wrong status values in the CSV."
        )
    )
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument(
        "--frame-id",
        action="append",
        default=[],
        help="Frame ID to verify. Repeat for multiple frames.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Verify every frame after the full review set has been checked.",
    )
    parser.add_argument("--reviewer", default="user")
    args = parser.parse_args()

    if not args.all and not args.frame_id:
        raise ValueError("Provide at least one --frame-id or use --all")

    rows = read_csv(args.ground_truth)
    requested = set(args.frame_id)
    known_frames = {row["frame_id"] for row in rows}
    missing = requested - known_frames
    if missing:
        raise ValueError(f"Unknown frame IDs: {sorted(missing)}")

    changed = 0
    for row in rows:
        if args.all or row["frame_id"] in requested:
            row["verification_status"] = "verified"
            row["label_source"] = f"manually_verified_by_{args.reviewer}"
            row["notes"] = "manually checked against the matching review image"
            changed += 1

    write_csv(args.ground_truth, rows)
    print(f"Marked {changed} slot labels as verified in {args.ground_truth}")


if __name__ == "__main__":
    main()
