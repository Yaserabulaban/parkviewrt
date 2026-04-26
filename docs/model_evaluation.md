# ParkViewRT Model Evaluation

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
yolov8n.pt
```

`yolov8n.pt` remains the production backend model for now. The comparison confirms that it correctly marks all labelled static slots as occupied, and the debug images were visually reliable for the current MMU parking images.

All compared models reached full slot accuracy on this small static-image set. Because the current test set is limited, the production choice also considers visual debug quality, existing backend compatibility, and the need to retest once real videos are available.

This decision should be revisited after real FCI and FAIE videos are collected, because video frames may include motion blur, lighting changes, different occupancy levels, and more occlusion.

## Model Summary

| Model | Locations | Total Detections | Avg Slot Accuracy | Avg Inference (ms) | Min Slot Overlap | Min Box Overlap |
| --- | --- | --- | --- | --- | --- | --- |
| yolov8n.pt | 2 | 124 | 100.00% | 1064.76 | 78.99% | 62.34% |
| yolo11n.pt | 2 | 138 | 100.00% | 884.84 | 79.93% | 61.45% |
| yolo26n.pt | 2 | 130 | 100.00% | 852.36 | 79.81% | 62.33% |

## Location Results

| Model | Location | Detections | Occupied | Available | Slot Accuracy | Inference (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| yolov8n.pt | FCI | 92 | 8 | 0 | 100.00% | 1284.18 |
| yolov8n.pt | FAIE | 32 | 8 | 0 | 100.00% | 845.34 |
| yolo11n.pt | FCI | 93 | 8 | 0 | 100.00% | 950.94 |
| yolo11n.pt | FAIE | 45 | 8 | 0 | 100.00% | 818.74 |
| yolo26n.pt | FCI | 91 | 8 | 0 | 100.00% | 947.00 |
| yolo26n.pt | FAIE | 39 | 8 | 0 | 100.00% | 757.73 |

## Selected Model Slot Details

| Location | Slot | Occupied | Slot Overlap | Box Overlap |
| --- | --- | --- | --- | --- |
| FCI | A1 | True | 89.44% | 74.30% |
| FCI | A2 | True | 92.93% | 74.11% |
| FCI | A3 | True | 85.88% | 70.81% |
| FCI | A4 | True | 93.29% | 73.34% |
| FCI | A5 | True | 78.99% | 71.78% |
| FCI | A6 | True | 80.51% | 71.45% |
| FCI | A7 | True | 85.56% | 68.30% |
| FCI | A8 | True | 82.46% | 70.78% |
| FAIE | B1 | True | 96.21% | 62.34% |
| FAIE | B2 | True | 93.05% | 68.73% |
| FAIE | B3 | True | 93.81% | 74.57% |
| FAIE | B4 | True | 94.51% | 67.73% |
| FAIE | B5 | True | 95.67% | 62.61% |
| FAIE | B6 | True | 91.92% | 67.42% |
| FAIE | B7 | True | 94.24% | 77.23% |
| FAIE | B8 | True | 87.35% | 86.70% |

## Generated Artifacts

The local evaluation run also creates:

```text
colab/outputs/model_comparison_summary.csv
colab/outputs/model_comparison_slots.csv
colab/outputs/debug_images/
```

The `colab/outputs/` folder is ignored by Git because it contains generated experiment artifacts.
