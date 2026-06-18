# ParkViewRT Model Evaluation Workflows

This folder contains repeatable scripts for preparing validation labels,
comparing pretrained YOLO models, and tuning occupancy thresholds.

## Active Dataset

ParkViewRT uses one active ground-truth file:

```text
colab/ground_truth/slot_status_ground_truth.csv
```

The dataset contains:

```text
FCI day: 11 frames, 858 labels
FCI night: 11 frames, 847 labels
FAIE day: 11 frames, 264 labels
FAIE night: 11 frames, 198 labels
Total: 44 frames, 2,167 monitored slot labels
```

Frame metadata is stored in:

```text
colab/ground_truth/frame_selection_summary.csv
```

## 1. Prepare The Dataset

Run from the repository root:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/prepare_validation_dataset.py
```

This command:

```text
selects 11 evenly spaced frames per video
uses runtime slot JSON files to create one row per monitored slot
reuses manually reviewed values already present in the active CSV
creates assisted preliminary labels for new rows
generates one debug image per selected frame
```

Review images:

```text
colab/outputs/validation/review_images/
```

## 2. Verify Ground Truth

Check every preliminary slot status against its matching review image. Correct
the `status` and `expected_status` columns when needed.

Verify one frame:

```powershell
py -3.11 colab/verify_ground_truth.py --frame-id fci_day_0
```

After all 44 frames have been checked:

```powershell
py -3.11 colab/verify_ground_truth.py --all
```

The evaluation scripts reject preliminary rows by default. The
`--allow-preliminary` option is diagnostic only and must not be used for final
report results.

## 3. Generate Label Distribution

```powershell
py -3.11 colab/report_label_distribution.py
```

Outputs:

```text
colab/outputs/validation/label_distribution.csv
colab/outputs/validation/label_distribution.md
```

The CSV contains overall, per-variant, and per-frame counts and percentages for
`available`, `occupied`, and `occluded`.

## 4. Compare Models

Local model weights:

```text
backend/app/models/yolo11n.pt
backend/app/models/yolo26n.pt
backend/app/models/yolo12n.pt
backend/app/models/yolov8n.pt
```

The active ground-truth rows are verified. Run:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/evaluate_model_accuracy.py
```

Outputs:

```text
colab/outputs/model_accuracy_summary.csv
colab/outputs/model_accuracy_frames.csv
colab/outputs/model_accuracy_slots.csv
```

The summary contains accuracy, status-level precision/recall/F1, false-status
counts, mismatches, detections, and average pipeline time.

## 5. Tune Thresholds

Run after choosing the strongest model:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/tune_thresholds.py --model yolo11n.pt
```

Replace `yolo11n.pt` if another model wins the comparison.

Default threshold grid:

```text
Confidence: 0.10 to 0.40
Slot overlap: 0.15 to 0.40
Box overlap: 0.10 to 0.30
Total combinations: 210
```

Outputs:

```text
colab/outputs/threshold_tuning_summary.csv
colab/outputs/threshold_tuning_mismatches.csv
```

## Current Runtime Status

The backend currently uses:

```text
Model: yolo11n.pt
Confidence: 0.20
Slot overlap: 0.25
Box overlap: 0.20
```

Final results:

```text
Selected model: yolo11n.pt
Model accuracy: 2,167 / 2,167 (100.00%)
Selected thresholds: 0.20 confidence, 0.25 slot overlap, 0.20 box overlap
Threshold accuracy: 2,167 / 2,167 (100.00%)
```

## Generated Files

`colab/outputs/` is ignored by Git. The output files can be regenerated from
the tracked videos, slot JSON files, frame selection CSV, and active
ground-truth CSV.
