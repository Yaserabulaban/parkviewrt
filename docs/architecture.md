# ParkViewRT Architecture

ParkViewRT is a web-based parking slot monitoring system for MMU parking areas. The current FYP2 implementation focuses on static-image processing while preparing the codebase for future video input.

## Technology Stack

```text
Frontend: React + Vite + TypeScript
Backend: FastAPI + Python
Computer Vision: Ultralytics YOLO, pretrained weights
Geometry: Shapely polygon and bounding-box overlap
Data Storage: JSON slot polygon files
```

## Active Project Structure

```text
backend/app/
  main.py
  settings.py
  api/routes/status.py
  services/yolo_detector.py
  services/occupancy.py
  services/video_snapshot.py
  data/images/
  data/slots/
  data/videos/
  data/outputs/

frontend/
  app/components/FCIParkingView.tsx
  app/components/FAIEParkingView.tsx
  hooks/useParkingStatus.ts
  api/parkingApi.ts
```

`backend/test_app` is not part of the active implementation.

## Current Processing Flow

1. The frontend requests `/api/status/{location_id}`.
2. FastAPI receives the request in `backend/app/api/routes/status.py`.
3. Backend defaults are loaded from `backend/app/settings.py`.
4. `ParkingOccupancyService` loads the correct slot JSON file.
5. The service loads the correct static parking image.
6. `YoloDetector` runs pretrained YOLO and filters detections to class `car`.
7. Each detected car bounding box is compared with each slot polygon.
8. A slot is marked occupied when one of the occupancy rules passes.
9. The backend returns total, occupied, available, and per-slot status.
10. The frontend updates the dashboard layout.

## Occupancy Decision Rules

For each slot polygon and detected car box, the backend calculates:

```text
slot overlap = intersection area / slot polygon area
box overlap  = intersection area / detection box area
```

A slot can be marked occupied by:

```text
slot overlap >= threshold
box overlap >= box_threshold
detection center inside slot polygon
slot centroid inside detection box
```

Current defaults:

```text
threshold = 0.30
box_threshold = 0.20
confidence = 0.20
image_size = 1600
```

The larger `image_size` is important because the parking images are wide and some vehicles are small in the original view.

These defaults are configured in `backend/app/settings.py` and can be overridden with:

```text
PARKVIEWRT_MODEL_PATH
PARKVIEWRT_CONFIDENCE
PARKVIEWRT_IMAGE_SIZE
PARKVIEWRT_SLOT_THRESHOLD
PARKVIEWRT_BOX_THRESHOLD
```

The active values can be checked with:

```text
GET /api/config
```

## Debug Flow

`/api/debug/{location_id}` runs the same detection and occupancy logic as `/api/status/{location_id}`, then draws:

```text
car bounding boxes
slot polygons
occupied or available color
overlap labels
summary information
```

This endpoint is used for visual validation and threshold tuning.

## Frontend Flow

The frontend uses `useParkingStatus(locationId)` to:

```text
fetch backend status
show loading and refresh states
store last updated time
provide manual refresh
```

The FCI and FAIE pages expose:

```text
Refresh button
Auto refresh switch
Last updated timestamp
Detection Debug link
Video Snapshot button
Video Samples button
Available and occupied counts
Slot layout visualization
```

## Current Limitations

```text
The current pipeline uses static images, not real-time video.
Pretrained YOLO may miss vehicles under trees, shadows, or unusual camera angles.
False positives may occur for non-car objects.
The slot polygons are manually prepared and tied to the current image perspective.
No database is used yet.
No custom model training has been performed yet.
```

## Future Video Direction

Initial video snapshot support is now available. The backend can read a sampled frame from a local video file and process it through the same occupancy logic as static images.

Video snapshot flow:

```text
video file -> selected frame -> YOLO detection -> slot overlap -> status response
```

The current endpoint is:

```text
GET /api/status/{location_id}/video-snapshot
```

Multi-frame sampling is also available:

```text
GET /api/status/{location_id}/video-samples
```

Video sampling flow:

```text
video file -> frame indices -> YOLO per frame -> per-frame occupancy -> majority-vote summary
```

Videos are expected under:

```text
backend/app/data/videos/{location_id}/
```

When real FCI and FAIE videos are obtained, the next step is to process frames periodically instead of only one requested snapshot.
