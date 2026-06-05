# ParkViewRT YOLO Model Evaluation

This document summarizes the current pretrained YOLO comparison for ParkViewRT.
The run compares the production model against current/latest suitable Ultralytics
nano detection checkpoints using the same backend thresholds and the current
runtime slot JSON files.

## Evaluation Setup

```text
Input images:
- backend/app/data/images/fci_day.png
- backend/app/data/images/fci_night.png
- backend/app/data/images/faie_day.png
- backend/app/data/images/faie_night.png

Runtime slot files:
- backend/app/data/slots/fci_day_slots.json
- backend/app/data/slots/fci_night_slots.json
- backend/app/data/slots/faie_day_slots.json
- backend/app/data/slots/faie_night_slots.json

Detection classes: car, truck
Confidence threshold: 0.20
Image size: 1600
Slot overlap threshold: 0.25
Box overlap threshold: 0.20
Runs per model/location/variant: 3 measured runs after 1 warmup run
```

## Compared Models

```text
yolo11n.pt  current production baseline
yolo26n.pt  latest Ultralytics production family, nano checkpoint
yolo12n.pt  newer attention-centric/community checkpoint, nano scale
yolov8n.pt  previous stable nano baseline for regression comparison
```

Ultralytics documents YOLO26 as the latest edge-oriented family, and documents
YOLO12 as a community/research line with production caveats. Because ParkViewRT
needs near-real-time dashboard inference, this comparison uses nano checkpoints
only instead of mixing nano/small/medium sizes.

## Important Limitation

These results are measured backend behavior, not final accuracy. The current
four reference images do not include manually verified ground-truth status for
every monitored slot. Therefore, the tables below should be used to justify a
practical model choice, then revisited once a labelled validation set of video
frames is prepared.

## Selected Model

```text
yolo11n.pt
```

`yolo11n.pt` remains the selected backend model for now.

Reason:

```text
It was the fastest model in the current run, matched YOLO26 on total detections,
detected more occupied FAIE day slots than YOLO26, and avoided the large latency
increase seen with YOLO12. YOLO26 remains the first model to retest when a
ground-truth validation set is available, but this run does not show enough
benefit to replace the stable current model.
```

## Model Summary

| Model | Variants | Total Detections | Occupied Slots | Available Slots | Occluded Slots | Avg Pipeline Time (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| yolo11n.pt | 4 | 124 | 41 | 149 | 7 | 649.69 |
| yolov8n.pt | 4 | 107 | 34 | 157 | 6 | 764.44 |
| yolo26n.pt | 4 | 124 | 42 | 148 | 7 | 775.51 |
| yolo12n.pt | 4 | 136 | 43 | 147 | 7 | 1185.13 |

## Variant Results

| Model | Location | Variant | Slots | Detections | Occupied | Available | Occluded | Avg Pipeline Time (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yolo11n.pt | FCI | day | 78 | 84 | 26 | 45 | 7 | 830.95 |
| yolo11n.pt | FCI | night | 77 | 3 | 1 | 76 | 0 | 577.76 |
| yolo11n.pt | FAIE | day | 24 | 34 | 14 | 10 | 0 | 575.32 |
| yolo11n.pt | FAIE | night | 18 | 3 | 0 | 18 | 0 | 614.75 |
| yolo26n.pt | FCI | day | 78 | 84 | 27 | 44 | 7 | 1090.75 |
| yolo26n.pt | FCI | night | 77 | 5 | 2 | 75 | 0 | 608.86 |
| yolo26n.pt | FAIE | day | 24 | 28 | 13 | 11 | 0 | 819.47 |
| yolo26n.pt | FAIE | night | 18 | 7 | 0 | 18 | 0 | 582.94 |
| yolo12n.pt | FCI | day | 78 | 85 | 27 | 44 | 7 | 1583.32 |
| yolo12n.pt | FCI | night | 77 | 11 | 2 | 75 | 0 | 968.39 |
| yolo12n.pt | FAIE | day | 24 | 34 | 14 | 10 | 0 | 1106.20 |
| yolo12n.pt | FAIE | night | 18 | 6 | 0 | 18 | 0 | 1082.62 |
| yolov8n.pt | FCI | day | 78 | 79 | 23 | 49 | 6 | 1066.56 |
| yolov8n.pt | FCI | night | 77 | 2 | 1 | 76 | 0 | 617.50 |
| yolov8n.pt | FAIE | day | 24 | 23 | 10 | 14 | 0 | 778.68 |
| yolov8n.pt | FAIE | night | 18 | 3 | 0 | 18 | 0 | 595.01 |

## Selected Model Variant Details

| Location | Variant | Slots | Detections | Occupied | Available | Occluded | Available Slot IDs | Occluded Slot IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FCI | day | 78 | 84 | 26 | 45 | 7 | A3 A9 A11 A13 A14 A18 A19 A20 A23 A24 A25 A26 A39 A40 A41 A42 A43 A44 A45 A46 A47 A48 A49 A51 A52 A53 A54 A56 A57 A58 A59 A63 A65 A66 A67 A68 A69 A71 A72 A73 A74 A75 A76 A77 A78 | A7 A10 A50 A60 A61 A62 A64 |
| FCI | night | 77 | 3 | 1 | 76 | 0 | A1 A2 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 A14 A15 A16 A17 A18 A19 A20 A21 A22 A23 A24 A25 A26 A27 A28 A29 A30 A31 A32 A33 A34 A35 A36 A37 A38 A39 A40 A41 A42 A43 A44 A45 A46 A47 A48 A49 A50 A51 A52 A53 A54 A55 A56 A57 A58 A59 A60 A61 A62 A63 A64 A65 A66 A67 A68 A69 A70 A71 A72 A73 A74 A75 A76 A77 | - |
| FAIE | day | 24 | 34 | 14 | 10 | 0 | B8 B13 B14 B15 B16 B24 B25 B26 B27 B29 | - |
| FAIE | night | 18 | 3 | 0 | 18 | 0 | B1 B2 B3 B4 B5 B6 B7 B8 B9 B10 B11 B12 B13 B14 B15 B24 B25 B26 | - |

## Generated Artifacts

```text
colab/outputs/model_comparison_summary.csv
colab/outputs/model_comparison_slots.csv
colab/outputs/debug_images/
```

The `colab/outputs/` folder is ignored by Git because it contains generated
experiment artifacts.

## Sources For Model Choice

- Ultralytics YOLO11 documentation: https://docs.ultralytics.com/models/yolo11/
- Ultralytics YOLO12 documentation: https://docs.ultralytics.com/models/yolo12/
- Ultralytics YOLO26 documentation: https://docs.ultralytics.com/models/yolo26/
