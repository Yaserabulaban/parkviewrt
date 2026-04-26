# ParkViewRT Colab Workflows

This folder is for notebook-based model evaluation and future training experiments.

Current notebook:

```text
evaluate_model.ipynb
```

Purpose:

```text
Compare pretrained YOLO models on FCI and FAIE parking images.
Measure detection count, slot occupancy accuracy, and inference time.
Export CSV results for FYP2 reporting.
```

Default models compared:

```text
yolov8n.pt
yolo11n.pt
yolo26n.pt
```

Custom training notebooks were removed for now because the current FYP2 phase uses pretrained YOLO only. Add a training notebook later when real video frames have been collected and annotated.
