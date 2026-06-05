# ParkViewRT Model Evaluation Workflows

This folder keeps repeatable YOLO comparison workflows for FYP2 reporting.
The current dashboard uses pretrained Ultralytics detection models only; no
custom YOLO training is part of the active implementation yet.

## Current Local Workflow

Run the comparison from the project root:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/evaluate_models.py --runs 3 --warmup-runs 1
```

Then regenerate the report:

```powershell
py -3.11 colab/generate_evaluation_report.py --selected-model yolo11n.pt
```

After validation frames have been extracted and manually verified, run the
accuracy comparison:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/evaluate_model_accuracy.py
```

To tune detection and slot-overlap thresholds for the selected model:

```powershell
$env:PYTHONPATH='backend'
py -3.11 colab/tune_thresholds.py
```

The comparison uses:

```text
backend/app/data/images/fci_day.png
backend/app/data/images/fci_night.png
backend/app/data/images/faie_day.png
backend/app/data/images/faie_night.png

backend/app/data/slots/fci_day_slots.json
backend/app/data/slots/fci_night_slots.json
backend/app/data/slots/faie_day_slots.json
backend/app/data/slots/faie_night_slots.json
```

Default models:

```text
yolo11n.pt
yolo26n.pt
yolo12n.pt
yolov8n.pt
```

`yolo11n.pt` is the current production baseline. `yolo26n.pt` is included as
the latest Ultralytics production family, `yolo12n.pt` is included as a newer
community/research checkpoint with production caveats, and `yolov8n.pt` is kept
as a previous stable nano baseline.

## Output Files

Generated outputs are written under:

```text
colab/outputs/
```

Expected files:

```text
model_comparison_summary.csv
model_comparison_slots.csv
debug_images/debug_yolo11n_fci_day.jpg
debug_images/debug_yolo11n_fci_night.jpg
debug_images/debug_yolo11n_faie_day.jpg
debug_images/debug_yolo11n_faie_night.jpg
debug_images/debug_yolo26n_fci_day.jpg
debug_images/debug_yolo26n_fci_night.jpg
debug_images/debug_yolo26n_faie_day.jpg
debug_images/debug_yolo26n_faie_night.jpg
debug_images/debug_yolo12n_fci_day.jpg
debug_images/debug_yolo12n_fci_night.jpg
debug_images/debug_yolo12n_faie_day.jpg
debug_images/debug_yolo12n_faie_night.jpg
debug_images/debug_yolov8n_fci_day.jpg
debug_images/debug_yolov8n_fci_night.jpg
debug_images/debug_yolov8n_faie_day.jpg
debug_images/debug_yolov8n_faie_night.jpg
```

The generated CSV and debug images are ignored by Git.

## How To Use The Results

Use `model_comparison_summary.csv` for measured behavior:

```text
detections
occupied_count
available_count
occluded_count
inference_ms_mean
```

Use `model_comparison_slots.csv` when you need to inspect individual slot
status, overlap ratio, box overlap ratio, and occupied reason.

Use the debug images to visually confirm whether the detections and slot
polygons match the parking area correctly. This is still important because the
current evaluation images do not include manual ground-truth status for every
slot.

For verified frame accuracy, use:

```text
model_accuracy_summary.csv
model_accuracy_frames.csv
model_accuracy_slots.csv
```

For threshold tuning, use:

```text
threshold_tuning_summary.csv
threshold_tuning_mismatches.csv
```

These files compare predictions against the verified labels in:

```text
colab/ground_truth/slot_status_ground_truth.csv
```

The script reads the original local videos using the `frame_index` values in
the ground-truth CSV, so extracted review images and generated outputs can be
deleted after the labels are verified.

## Current Decision

The current measured run keeps `yolo11n.pt` as the backend model.

Reason:

```text
yolo11n.pt achieved the best verified validation-frame accuracy, had perfect
occupied recall on the reviewed frames, and avoided YOLO12's higher latency.
YOLO26 should be retested again if the validation set is expanded.
```

The threshold sweep keeps the current backend defaults:

```text
PARKVIEWRT_CONFIDENCE=0.20
PARKVIEWRT_SLOT_THRESHOLD=0.25
PARKVIEWRT_BOX_THRESHOLD=0.20
```

## Notebook

```text
evaluate_model.ipynb
```

The notebook is retained for Colab-style experiments, but the local script is
the current source of truth because it uses the latest runtime day/night files.

## Model Weights

Weights are stored locally under:

```text
backend/app/models/
```

The scripts may download missing `.pt` files. Model weights are ignored by Git.
