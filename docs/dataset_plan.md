# ParkViewRT Dataset Plan

This document describes the current data setup and the plan for using real FCI and FAIE parking videos when they become available.

## Current Data

Static parking images:

```text
backend/app/data/images/fci.jpeg
backend/app/data/images/faie.jpeg
```

Slot polygon files:

```text
backend/app/data/slots/fci_slots.json
backend/app/data/slots/faie_slots.json
```

Slot file format:

```json
{
  "location_id": "fci",
  "slots": [
    {
      "slot_id": "A1",
      "points": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    }
  ]
}
```

Current status:

```text
FCI slot polygons are prepared and validated.
FAIE slot polygons are prepared and validated.
Static images are used as a temporary replacement for real video frames.
Pretrained YOLO is used without custom training.
```

## Current Model Approach

The project currently uses:

```text
YOLO pretrained model: yolo11n.pt
Detection class: car only
No custom dataset training yet
```

The model weights are stored locally but ignored by Git:

```text
backend/app/models/yolo11n.pt
```

If missing, Ultralytics can download the weights when network access is available.

The active model and detection defaults are configured through environment variables:

```text
PARKVIEWRT_MODEL_PATH=backend/app/models/yolo11n.pt
PARKVIEWRT_CONFIDENCE=0.20
PARKVIEWRT_IMAGE_SIZE=1600
PARKVIEWRT_SLOT_THRESHOLD=0.30
PARKVIEWRT_BOX_THRESHOLD=0.20
```

These defaults are documented in `.env.example`.

## Real Video Requirements

When real parking videos are obtained, the preferred requirements are:

```text
Separate videos for FCI and FAIE
Camera angle should be fixed
Camera should cover the same slots as the polygon JSON
Video should include normal daytime parking conditions
Video should include both occupied and available slot examples
Resolution should be high enough for small parked cars to remain visible
```

Recommended collection conditions:

```text
morning
afternoon
different occupancy levels
clear weather
partial occlusion cases if available
```

Avoid changing camera position after slot polygons are created. If the camera moves, the slot polygons must be recreated.

## Planned Video Processing Flow

The first video flow is now a snapshot pipeline:

```text
load video
select one frame by frame_index
run YOLO on sampled frame
compare detections with slot polygons
return occupancy status
```

The current endpoint is:

```text
GET /api/status/{location_id}/video-snapshot
```

Videos should be placed in:

```text
backend/app/data/videos/{location_id}/
```

The current implementation reuses shared logic for:

```text
static image status
single video frame status
single video snapshot status
```

Future real-time behavior should extend this by sampling frames periodically:

```text
load video or stream
sample one frame every N frames or every N seconds
run existing frame occupancy logic
publish latest occupancy status
```

The current backend also supports a multi-frame test endpoint:

```text
GET /api/status/{location_id}/video-samples
```

This endpoint samples a fixed number of frames from a local video and calculates an aggregated occupancy summary using majority voting across sampled frames.

## Future Dataset Expansion

If pretrained YOLO is not accurate enough for the final demo, the next dataset step is to prepare a custom detection dataset.

Potential custom dataset labels:

```text
car
```

Possible annotation format:

```text
YOLO bounding-box format
```

Suggested training data:

```text
frames sampled from FCI videos
frames sampled from FAIE videos
different lighting and occupancy conditions
cars partially covered by trees or shadows
small far-away vehicles
```

Training is not part of the current phase. It should only be considered after testing real videos with the pretrained model.

## Data Storage Policy

Git should track:

```text
slot JSON files
small representative static images if needed
documentation
source code
```

Git should ignore:

```text
large videos
generated output images
model weights
virtual environments
build folders
```

The current `.gitignore` excludes:

```text
backend/app/data/videos/
backend/app/data/outputs/
*.pt
*.pth
*.onnx
```
