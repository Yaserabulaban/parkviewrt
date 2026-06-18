# Report Update Summary After Supervisor Feedback

## Validation Dataset

The project uses 11 evenly spaced frames from each video variant.

| Location | Variant | Frames | Monitored Slots | Verified Labels |
| --- | --- | ---: | ---: | ---: |
| FCI | day | 11 | 78 | 858 |
| FCI | night | 11 | 77 | 847 |
| FAIE | day | 11 | 24 | 264 |
| FAIE | night | 11 | 18 | 198 |
| **Total** |  | **44** |  | **2,167** |

All 2,167 labels were manually reviewed. Unmonitored dashboard-only slots are
excluded.

## Label Distribution

| Status | Count | Percentage |
| --- | ---: | ---: |
| Available | 1,009 | 46.56% |
| Occupied | 1,106 | 51.04% |
| Occluded | 52 | 2.40% |

### Distribution By Variant

| Location | Variant | Available | Occupied | Occluded |
| --- | --- | ---: | ---: | ---: |
| FCI | day | 16 (1.86%) | 790 (92.07%) | 52 (6.06%) |
| FCI | night | 763 (90.08%) | 84 (9.92%) | 0 |
| FAIE | day | 87 (32.95%) | 177 (67.05%) | 0 |
| FAIE | night | 143 (72.22%) | 55 (27.78%) | 0 |

Available and occupied labels are close overall, but variant-level occupancy
reflects the actual source videos. Occluded labels are naturally rare.

## Model Comparison

| Model | Correct | Mismatches | Accuracy | Avg Pipeline Time |
| --- | ---: | ---: | ---: | ---: |
| yolo11n.pt | 2,167 | 0 | 100.00% | 515.63 ms |
| yolo12n.pt | 2,140 | 27 | 98.75% | 877.83 ms |
| yolo26n.pt | 2,070 | 97 | 95.52% | 541.59 ms |
| yolov8n.pt | 2,033 | 134 | 93.82% | 601.09 ms |

### Selected Model

```text
yolo11n.pt
```

It achieved perfect slot-status accuracy and the lowest average pipeline time.

## Threshold Tuning

The sweep tested 210 combinations:

```text
Confidence: 0.10 to 0.40
Slot overlap: 0.15 to 0.40
Box overlap: 0.10 to 0.30
```

| Confidence | Best Correct | Accuracy | Perfect Combinations |
| ---: | ---: | ---: | ---: |
| 0.10 | 2,150 | 99.22% | 0 |
| 0.15 | 2,157 | 99.54% | 0 |
| 0.20 | 2,167 | 100.00% | 30 |
| 0.25 | 2,147 | 99.08% | 0 |
| 0.30 | 2,129 | 98.25% | 0 |
| 0.35 | 2,109 | 97.32% | 0 |
| 0.40 | 2,077 | 95.85% | 0 |

### Selected Thresholds

```text
Confidence: 0.20
Slot overlap: 0.25
Box overlap: 0.20
```

The selected combination achieved 2,167/2,167 correct labels with no false
available, false occupied, or false occluded results. It is retained because it
matches the best measured accuracy and is already used by the runtime backend.

## Files Changed Or Added

```text
colab/prepare_validation_dataset.py
colab/report_label_distribution.py
colab/verify_ground_truth.py
colab/evaluate_model_accuracy.py
colab/tune_thresholds.py
colab/ground_truth/frame_selection_summary.csv
colab/ground_truth/slot_status_ground_truth.csv
colab/README.md
docs/model_evaluation.md
docs/testing_plan.md
docs/dataset_plan.md
docs/report_update_summary_after_supervisor_feedback.md
README.md
```

## Generated Evidence

```text
colab/outputs/validation/review_images/
colab/outputs/validation/label_distribution.csv
colab/outputs/validation/label_distribution.md
colab/outputs/model_accuracy_summary.csv
colab/outputs/model_accuracy_frames.csv
colab/outputs/model_accuracy_slots.csv
colab/outputs/model_accuracy_mismatches.csv
colab/outputs/threshold_tuning_summary.csv
colab/outputs/threshold_tuning_mismatches.csv
```

## Commands Run

```powershell
py -3.11 colab/verify_ground_truth.py --all --reviewer user
py -3.11 colab/report_label_distribution.py

$env:PYTHONPATH='backend'
py -3.11 colab/evaluate_model_accuracy.py
py -3.11 colab/tune_thresholds.py --model yolo11n.pt
py -3.11 -m pytest backend/app/tests
```

## Final Decisions

```text
Selected model: yolo11n.pt
Selected confidence threshold: 0.20
Selected slot overlap threshold: 0.25
Selected box overlap threshold: 0.20
```
