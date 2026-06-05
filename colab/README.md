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

## Current Decision

The current measured run keeps `yolo11n.pt` as the backend model.

Reason:

```text
yolo11n.pt was fastest in the current run, matched YOLO26 on total detections,
detected more occupied FAIE day slots than YOLO26, and avoided YOLO12's higher
latency. YOLO26 should be retested after a labelled validation frame set exists.
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
