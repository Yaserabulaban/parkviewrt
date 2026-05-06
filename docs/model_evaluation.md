# ParkViewRT Model Evaluation

This document summarizes the pretrained YOLO model comparison that was run earlier on the original FCI and FAIE static parking images.

The current application flow has moved to video-frame occupancy. Keep this report as the baseline pretrained-model comparison, then rerun evaluation after the final stable FCI and FAIE videos are captured and labeled.

## Evaluation Setup

```text
Input images: backend/app/data/images/fci.jpeg, backend/app/data/images/faie.jpeg
Slot labels: backend/app/data/slots/fci_slots.json, backend/app/data/slots/faie_slots.json
Detection classes in current backend: car, truck
Confidence threshold: 0.20
Image size: 1600
Slot overlap threshold: 0.30
Box overlap threshold: 0.20
```

The original labelled static-image comparison used eight selected slots for each location, and those selected slots were treated as occupied for the comparison. The current runtime slot files are broader: FCI monitors 79 slots and FAIE monitors 40 slots.

## Selected Model

```text
yolo11n.pt
```

`yolo11n.pt` remains the production backend model for now. The baseline comparison confirmed that it correctly marked all labelled static slots as occupied, and the debug images were visually reliable for the original MMU parking images.

All compared models reached full slot accuracy on this small static-image set. Because the current test set is limited, the production choice also considers visual debug quality, existing backend compatibility, and the need to retest once real videos are available.

This decision should be revisited after the final stable FCI and FAIE videos are collected, because video frames may include motion blur, lighting changes, different occupancy levels, and more occlusion.

## Model Summary

| Model | Locations | Total Detections | Avg Slot Accuracy | Avg Inference (ms) | Min Slot Overlap | Min Box Overlap |
| --- | --- | --- | --- | --- | --- | --- |
| yolo11n.pt | 2 | 138 | 100.00% | 884.84 | 79.93% | 61.45% |
| yolo26n.pt | 2 | 130 | 100.00% | 852.36 | 79.81% | 62.33% |
| yolov8n.pt | 2 | 124 | 100.00% | 1064.76 | 78.99% | 62.34% |

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
| FCI | A1 | True | 89.16% | 72.62% |
| FCI | A2 | True | 93.09% | 74.23% |
| FCI | A3 | True | 86.16% | 71.03% |
| FCI | A4 | True | 93.27% | 73.26% |
| FCI | A5 | True | 80.56% | 71.51% |
| FCI | A6 | True | 79.93% | 71.93% |
| FCI | A7 | True | 82.84% | 70.51% |
| FCI | A8 | True | 84.46% | 69.49% |
| FAIE | B1 | True | 96.29% | 61.45% |
| FAIE | B2 | True | 93.40% | 69.40% |
| FAIE | B3 | True | 93.23% | 74.71% |
| FAIE | B4 | True | 93.57% | 68.62% |
| FAIE | B5 | True | 96.03% | 62.62% |
| FAIE | B6 | True | 93.08% | 66.77% |
| FAIE | B7 | True | 93.15% | 78.22% |
| FAIE | B8 | True | 86.11% | 86.84% |

## Generated Artifacts

The local evaluation run also creates:

```text
colab/outputs/model_comparison_summary.csv
colab/outputs/model_comparison_slots.csv
colab/outputs/debug_images/
```

The `colab/outputs/` folder is ignored by Git because it contains generated experiment artifacts.
