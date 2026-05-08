# ParkViewRT Dataset Plan

This document describes the current data setup and the plan for maintaining FCI and FAIE parking footage.

## Current Data

Tracked reference images:

```text
backend/app/data/images/fci_day.png
backend/app/data/images/fci_night.png
backend/app/data/images/faie.jpeg
```

Tracked slot polygon files:

```text
backend/app/data/slots/fci_day_slots.json
backend/app/data/slots/fci_night_slots.json
backend/app/data/slots/faie_slots.json
```

Tracked FCI annotation source exports:

```text
backend/app/data/slots/fci_day_annotations.json
backend/app/data/slots/fci_night_annotations.json
```

Ignored local videos:

```text
backend/app/data/videos/fci/
backend/app/data/videos/faie/
```

Ignored generated outputs:

```text
backend/app/data/outputs/
colab/outputs/
frontend/dist/
```

## Slot File Format

```json
{
  "location_id": "fci",
  "layout_type": "video_day_frame",
  "slots": [
    {
      "slot_id": "A1",
      "row": "A",
      "shape": "polygon",
      "points": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    }
  ]
}
```

## Current Slot Coverage

```text
FCI day: A1-A75, 75 monitored slots
FCI night: A1-A77, 77 monitored slots
FAIE: B1-B40, 40 monitored slots
```

FCI runtime polygons are selected by video variant. `fci_day_slots.json` is generated from `fci_day_annotations.json`; `fci_night_slots.json` is generated from `fci_night_annotations.json`. If FCI is retaken from a different angle, regenerate the matching day or night runtime slot file.

FAIE polygons currently cover the full displayed `B1-B40` layout.

## Current Model Approach

```text
YOLO pretrained model: yolo11n.pt
Detection classes: car, truck
Custom training: not used yet
```

The backend model weights are expected locally under:

```text
backend/app/models/yolo11n.pt
```

Model weights are ignored by Git. If missing, Ultralytics may download them when network access is available.

Detection defaults:

```text
PARKVIEWRT_MODEL_PATH=backend/app/models/yolo11n.pt
PARKVIEWRT_CONFIDENCE=0.20
PARKVIEWRT_IMAGE_SIZE=1600
PARKVIEWRT_SLOT_THRESHOLD=0.25
PARKVIEWRT_BOX_THRESHOLD=0.20
```

## Video Collection Requirements

Use separate videos for:

```text
FCI parking
FAIE parking
```

Recommended capture conditions:

```text
fixed tripod or stable mounting
no camera movement after labeling starts
daytime lighting or clear, stable night lighting
high enough resolution for distant vehicles
examples of both occupied and available slots
minimal tree or pole obstruction where possible
```

Avoid zooming, panning, or moving the tripod after slot polygons are created. A small angle change can make the polygons inaccurate.

## Video Processing Flow

Current dashboard flow:

```text
local video -> current playback time -> frame_index -> YOLO -> slot polygons -> dashboard status
```

Current backend endpoints:

```text
GET /api/video/{location_id}/metadata?variant=day
GET /api/video/{location_id}?variant=day
GET /api/status/{location_id}/video-snapshot?variant=day
GET /api/status/{location_id}/video-samples?variant=day
GET /api/debug/{location_id}?source=video&variant=day
```

The frame status cache is generated under:

```text
backend/app/data/outputs/video_status_cache/
```

Clear the relevant cache folder after replacing a video with the same filename.

## Future Dataset Expansion

If pretrained YOLO is not accurate enough for final evaluation, prepare a custom detection dataset from sampled video frames.

Potential labels:

```text
car
truck
```

Recommended frames:

```text
FCI and FAIE videos from the final capture conditions
different occupancy levels
small distant vehicles
partial tree cover or shadows
empty slots for negative examples
```

Training is not part of the current phase. It should only be considered after the final stable videos are tested with the pretrained model.

## Data Storage Policy

Git should track:

```text
source code
slot JSON files
small reference images
documentation
tests
```

Git should ignore:

```text
large videos
generated debug images
frame status cache
model weights
virtual environments
build folders
logs
```
