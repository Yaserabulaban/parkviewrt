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
YOLO pretrained model: yolov8n.pt
Detection class: car only
No custom dataset training yet
```

The model weights are stored locally but ignored by Git:

```text
backend/app/models/yolov8n.pt
```

If missing, Ultralytics can download the weights when network access is available.

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

The intended video flow is:

```text
load video
sample one frame every N frames or every N seconds
run YOLO on sampled frame
compare detections with slot polygons
return latest occupancy status
```

The existing static image occupancy service should be reused by extracting shared logic for:

```text
process_image(location_id, image_path)
process_frame(location_id, frame)
process_video_snapshot(location_id, video_path)
```

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
