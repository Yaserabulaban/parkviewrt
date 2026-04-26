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
  api/routes/status.py
  services/yolo_detector.py
  services/occupancy.py
  data/images/
  data/slots/
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
3. `ParkingOccupancyService` loads the correct slot JSON file.
4. The service loads the correct static parking image.
5. `YoloDetector` runs pretrained YOLO and filters detections to class `car`.
6. Each detected car bounding box is compared with each slot polygon.
7. A slot is marked occupied when one of the occupancy rules passes.
8. The backend returns total, occupied, available, and per-slot status.
9. The frontend updates the dashboard layout.

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
Last updated timestamp
Detection Debug link
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

When real videos are obtained, the planned backend flow is:

```text
video input -> frame sampling -> YOLO detection -> slot overlap -> status response
```

The existing occupancy logic should be reused for both images and sampled video frames.
