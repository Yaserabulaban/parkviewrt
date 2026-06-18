# ParkViewRT YOLO Model Evaluation

This document records the final pretrained-model comparison and threshold
tuning results for the active ParkViewRT validation dataset.

## Validation Dataset

The dataset uses an equal 11 frames from each video variant.

| Location | Variant | Frames | Monitored Slots Per Frame | Verified Labels |
| --- | --- | ---: | ---: | ---: |
| FCI | day | 11 | 78 | 858 |
| FCI | night | 11 | 77 | 847 |
| FAIE | day | 11 | 24 | 264 |
| FAIE | night | 11 | 18 | 198 |
| **Total** |  | **44** |  | **2,167** |

All 2,167 labels were manually reviewed before the final evaluation.
Unmonitored dashboard-only slots are excluded.

Tracked files:

```text
colab/ground_truth/frame_selection_summary.csv
colab/ground_truth/slot_status_ground_truth.csv
```

## Label Distribution

| Status | Count | Percentage |
| --- | ---: | ---: |
| Available | 1,009 | 46.56% |
| Occupied | 1,106 | 51.04% |
| Occluded | 52 | 2.40% |

### Distribution By Variant

| Location | Variant | Labels | Available | Occupied | Occluded |
| --- | --- | ---: | ---: | ---: | ---: |
| FCI | day | 858 | 16 (1.86%) | 790 (92.07%) | 52 (6.06%) |
| FCI | night | 847 | 763 (90.08%) | 84 (9.92%) | 0 (0.00%) |
| FAIE | day | 264 | 87 (32.95%) | 177 (67.05%) | 0 (0.00%) |
| FAIE | night | 198 | 143 (72.22%) | 55 (27.78%) | 0 (0.00%) |

Available and occupied labels are close overall. Individual variants have
different distributions because they represent real parking conditions.
Occluded labels are naturally less common and occur in FCI day.

## Compared Models

```text
yolo11n.pt
yolo26n.pt
yolo12n.pt
yolov8n.pt
```

All models used:

```text
Detection classes: car and truck
Confidence threshold: 0.20
Image size: 1600
Slot overlap threshold: 0.25
Box overlap threshold: 0.20
```

## Model Comparison Results

| Model | Correct | Mismatches | Accuracy | Occupied P/R/F1 | Available P/R/F1 | Occluded P/R/F1 | Avg Pipeline Time |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| yolo11n.pt | 2,167 | 0 | 100.00% | 100.00 / 100.00 / 100.00% | 100.00 / 100.00 / 100.00% | 100.00 / 100.00 / 100.00% | 515.63 ms |
| yolo12n.pt | 2,140 | 27 | 98.75% | 99.09 / 98.46 / 98.78% | 98.82 / 99.80 / 99.31% | 89.80 / 84.62 / 87.13% | 877.83 ms |
| yolo26n.pt | 2,070 | 97 | 95.52% | 99.90 / 91.32 / 95.42% | 93.25 / 100.00 / 96.51% | 68.92 / 98.08 / 80.95% | 541.59 ms |
| yolov8n.pt | 2,033 | 134 | 93.82% | 99.29 / 88.52 / 93.59% | 89.91 / 99.80 / 94.60% | 77.05 / 90.38 / 83.19% | 601.09 ms |

### False Status Counts

| Model | False Available | False Occupied | False Occluded |
| --- | ---: | ---: | ---: |
| yolo11n.pt | 0 | 0 | 0 |
| yolo12n.pt | 12 | 10 | 5 |
| yolo26n.pt | 73 | 1 | 23 |
| yolov8n.pt | 113 | 7 | 14 |

Most mismatches from YOLO26 and YOLOv8 are occupied slots predicted as
available. This error is important because it can tell a driver that an
occupied space is free.

## Selected Model

```text
yolo11n.pt
```

`yolo11n.pt` remains selected because it classified all 2,167 verified slot
labels correctly. It also had the lowest measured average pipeline time among
the compared models. YOLO12 was the second most accurate but was considerably
slower and produced 27 mismatches.

## Threshold Tuning

The selected model was tested using:

```text
Confidence thresholds: 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40
Slot overlap thresholds: 0.15, 0.20, 0.25, 0.30, 0.35, 0.40
Box overlap thresholds: 0.10, 0.15, 0.20, 0.25, 0.30
Total combinations: 210
```

### Results By Confidence

| Confidence | Best Correct Labels | Best Accuracy | Perfect Combinations |
| ---: | ---: | ---: | ---: |
| 0.10 | 2,150 / 2,167 | 99.22% | 0 |
| 0.15 | 2,157 / 2,167 | 99.54% | 0 |
| 0.20 | 2,167 / 2,167 | 100.00% | 30 |
| 0.25 | 2,147 / 2,167 | 99.08% | 0 |
| 0.30 | 2,129 / 2,167 | 98.25% | 0 |
| 0.35 | 2,109 / 2,167 | 97.32% | 0 |
| 0.40 | 2,077 / 2,167 | 95.85% | 0 |

The ranking function placed `confidence=0.20`, `slot=0.40`, and `box=0.30`
first. However, 30 combinations achieved the same perfect result at confidence
`0.20`.

## Selected Thresholds

```text
Confidence threshold: 0.20
Slot overlap threshold: 0.25
Box overlap threshold: 0.20
```

The existing production combination also achieved:

```text
Correct labels: 2,167 / 2,167
Accuracy: 100.00%
Occupied precision/recall/F1: 100.00%
Available precision/recall/F1: 100.00%
Occluded precision/recall/F1: 100.00%
False available: 0
False occupied: 0
False occluded: 0
Average pipeline time: 521.65 ms
```

The existing values are retained because they are perfectly accurate on the
verified dataset, moderate rather than aggressive, and already used by the
runtime backend. Increasing the overlap thresholds does not improve the
measured result.

## Generated Evidence

```text
colab/outputs/validation/label_distribution.csv
colab/outputs/validation/label_distribution.md
colab/outputs/model_accuracy_summary.csv
colab/outputs/model_accuracy_frames.csv
colab/outputs/model_accuracy_slots.csv
colab/outputs/model_accuracy_mismatches.csv
colab/outputs/threshold_tuning_summary.csv
colab/outputs/threshold_tuning_mismatches.csv
```
