# ParkViewRT Architecture

ParkViewRT is a web-based parking slot monitoring system for MMU parking areas. The current FYP2 implementation is video-dashboard focused: the frontend plays local FCI and FAIE footage, the backend samples video frames, YOLO detects vehicles, and slot polygons convert detections into occupied/free slot status.

## Technology Stack

```text
Frontend: React + Vite + TypeScript
Backend: FastAPI + Python
Computer vision: Ultralytics YOLO
Geometry: Shapely polygon and bounding-box overlap
Data storage: JSON slot polygon files plus generated local cache files
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
  services/slot_layouts.py
  tools/generate_video_slot_layouts.py
  tools/cache_video_status.py
  data/images/
  data/slots/
  data/videos/      ignored by Git
  data/outputs/     ignored by Git

frontend/
  app/components/FCIParkingView.tsx
  app/components/FAIEParkingView.tsx
  app/components/ParkingVideoPreview.tsx
  hooks/useParkingStatus.ts
  api/parkingApi.ts
```

## Current Processing Flow

1. The dashboard loads the parking page for `fci` or `faie`.
2. `ParkingVideoPreview` requests `/api/video/{location_id}/metadata`, then plays `/api/video/{location_id}`.
3. The frontend converts the current video timestamp to a frame index using the reported FPS.
4. `useParkingStatus` requests `/api/status/{location_id}/video-snapshot?frame_index=...`.
5. `VideoSnapshotService` reads the requested frame from the selected local video.
6. `ParkingOccupancyService` runs YOLO on that frame.
7. The detector keeps vehicle classes `car` and `truck`.
8. Vehicle boxes are compared with slot polygons loaded from `backend/app/data/slots/{location_id}_slots.json`.
9. The backend returns occupied/free slot status, counts, source metadata, and cache state.
10. The frontend updates the visual parking layout.

The static image endpoint still exists for compatibility, but the current dashboard flow uses video snapshots by default.

## Occupancy Decision Rules

For each slot polygon and detected vehicle box, the backend calculates:

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
model = backend/app/models/yolo11n.pt
```

These values come from `backend/app/settings.py` and can be overridden with:

```text
PARKVIEWRT_MODEL_PATH
PARKVIEWRT_CONFIDENCE
PARKVIEWRT_IMAGE_SIZE
PARKVIEWRT_SLOT_THRESHOLD
PARKVIEWRT_BOX_THRESHOLD
```

## Slot Coverage

```text
FCI display slots: A1-A80
FCI monitored slots: A1-A80 except A77
FAIE display slots: B1-B40
FAIE monitored slots: B1-B40
```

`A77` is intentionally excluded because it is not a usable parking slot in the current FCI layout.

## Video and Cache Behavior

Videos are local files under:

```text
backend/app/data/videos/{location_id}/
```

Supported extensions:

```text
.mp4
.avi
.mov
.mkv
```

The backend serves videos through `/api/video/{location_id}` with no-cache headers. The frontend also appends a version token based on file size and last modified time so replacing a video with the same filename refreshes correctly in the browser.

Frame status results are saved under:

```text
backend/app/data/outputs/video_status_cache/
```

This cache is generated data and is ignored by Git. Clear the matching location/video cache after replacing a video with the same filename if old analysis results should not be reused.

## Debug Flow

`/api/debug/{location_id}` returns a JPEG overlay. By default it draws the requested video frame:

```text
GET /api/debug/fci?source=video&frame_index=0
```

Static image debug is still available:

```text
GET /api/debug/fci?source=static
```

The debug image includes vehicle boxes, slot polygons, occupied/free colors, overlap labels, and a summary bar.

## Current Limitations

```text
Slot polygons are tied to the camera angle used during labeling.
If the tripod or camera angle changes, slot JSON files must be regenerated.
Pretrained YOLO can miss small, shaded, occluded, or distant vehicles.
Frame-by-frame analysis is slower than raw video playback on some machines.
No database or persistent server-side history is used yet.
No custom YOLO training has been performed yet.
```
