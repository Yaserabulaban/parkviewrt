# ParkViewRT Colab Workflows

This folder is for notebook-based model evaluation and future training experiments.

## Current Notebook

```text
evaluate_model.ipynb
```

Purpose:

```text
Compare pretrained YOLO models on FCI and FAIE parking images.
Measure detection count, slot occupancy accuracy, and inference time.
Export CSV results and annotated debug images for FYP2 reporting.
```

Default models compared:

```text
yolov8n.pt
yolo11n.pt
yolo26n.pt
```

## How To Run In Colab

1. Open `evaluate_model.ipynb` in Google Colab.
2. Enable GPU from `Runtime > Change runtime type > T4 GPU`.
3. Clone or upload the `parkviewrt` project into `/content/parkviewrt`.
4. Run all cells from top to bottom.
5. Check the output folder:

```text
colab/outputs/
```

Expected output files:

```text
model_comparison_summary.csv
model_comparison_slots.csv
debug_yolov8n_fci.jpg
debug_yolov8n_faie.jpg
debug_yolo11n_fci.jpg
debug_yolo11n_faie.jpg
debug_yolo26n_fci.jpg
debug_yolo26n_faie.jpg
```

## How To Use The Results

Use `model_comparison_summary.csv` to choose the best pretrained model based on:

```text
slot_accuracy
inference_ms
detections
occupied_count
available_count
```

Use the debug images to visually confirm whether the model is detecting the correct cars and whether the slot occupancy logic matches the parking polygons.

## Current Decision

Based on the current FCI and FAIE comparison run, `yolov8n.pt` is kept as the production backend model for now.

Reason:

```text
It gives correct occupancy on the labelled static slots and the debug output is visually reliable for the current MMU images.
```

This decision can be revisited after real FCI and FAIE parking videos are collected.

Custom training notebooks were removed for now because the current FYP2 phase uses pretrained YOLO only. Add a training notebook later when real video frames have been collected and annotated.
