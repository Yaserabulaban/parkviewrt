# ParkViewRT API Contract

The frontend currently points to:

```text
http://127.0.0.1:8001
```

If the backend runs on another port, update `frontend/config/env.ts`.

## Health Check

```text
GET /api/health
```

Purpose: confirm that the backend is running and the detector object exists.

Example response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "locations": ["fci", "faie"]
}
```

## Backend Configuration

```text
GET /api/config
```

Purpose: expose active detection settings and slot layout metadata.

Example response:

```json
{
  "detection": {
    "model_path": "backend/app/models/yolo11n.pt",
    "confidence_threshold": 0.2,
    "image_size": 1600,
    "slot_overlap_threshold": 0.25,
    "box_overlap_threshold": 0.2
  },
  "locations": ["fci", "faie"],
  "slot_layouts": {
    "fci": {
      "display_slot_ids": ["A1", "A2"],
      "monitored_slot_ids": ["A1", "A2"],
      "default_variant": "day",
      "variants": {
        "day": {
          "display_slot_ids": ["A1", "A2"],
          "monitored_slot_ids": ["A1", "A2"]
        },
        "night": {
          "display_slot_ids": ["A1", "A2"],
          "monitored_slot_ids": ["A1", "A2"]
        }
      }
    }
  }
}
```

## Static Parking Status

```text
GET /api/status/{location_id}
```

Supported locations:

```text
fci
faie
```

Purpose: run YOLO on the static reference image and compare detections with slot polygons. This endpoint is retained for backend testing and comparison. The dashboard uses video snapshots by default.

Optional query parameters:

```text
threshold      Slot polygon overlap threshold. Default: 0.25
box_threshold  Detection-box overlap threshold. Default: 0.20
confidence     YOLO confidence threshold. Default: 0.20
image_size     YOLO inference image size. Default: 1600
variant        day or night. Default: day
```

Example response:

```json
{
  "location_id": "fci",
  "total_slots": 75,
  "occupied_count": 61,
  "available_count": 14,
  "slots": [
    { "slot_id": "A1", "occupied": true },
    { "slot_id": "A2", "occupied": false }
  ]
}
```

## Demo Random Status

```text
GET /api/status/{location_id}/demo
```

Purpose: generate repeatable or random dashboard data without running YOLO.

Optional query parameters:

```text
occupancy_rate  Occupied probability per slot. Default: 0.5
seed            Optional integer for repeatable output
variant         day or night. Default: day
```

Example:

```text
GET /api/status/fci/demo?occupancy_rate=0.6&seed=7
GET /api/status/fci/demo?variant=night&occupancy_rate=0.6&seed=7
GET /api/status/faie/demo?variant=night&occupancy_rate=0.6&seed=7
```

## Video Metadata

```text
GET /api/video/{location_id}/metadata
```

Purpose: return the selected local video details used by the frontend for playback sync and cache busting.

Optional query parameters:

```text
variant        day or night. Default: day
```

Example response:

```json
{
  "location_id": "fci",
  "variant": "day",
  "video_path": "backend/app/data/videos/fci/fci_video.mov",
  "file_name": "fci_video.mov",
  "file_size": 668794432,
  "last_modified": 1778094931.0,
  "frame_count": 19522,
  "fps": 29.97,
  "duration_seconds": 651.38
}
```

## Video File

```text
GET /api/video/{location_id}
```

Purpose: serve the selected local video to the dashboard. The response uses no-cache headers so replacing a video with the same filename is reflected in the browser.

Optional query parameters:

```text
variant        day or night. Default: day
```

Supported video extensions:

```text
.mp4
.avi
.mov
.mkv
```

## Video Snapshot Status

```text
GET /api/status/{location_id}/video-snapshot
```

Purpose: read one frame from the selected local video, run YOLO and slot overlap logic, return a normal parking status response, and optionally save or reuse a cached frame result.

Optional query parameters:

```text
frame_index     Frame number to sample. Default: 0
debug           Include a generated debug image path. Default: false
use_cache       Reuse a saved result when available. Default: true
save_result     Save the frame result under data/outputs. Default: true
threshold       Slot polygon overlap threshold. Default: configured backend value
box_threshold   Detection-box overlap threshold. Default: configured backend value
confidence      YOLO confidence threshold. Default: configured backend value
image_size      YOLO inference image size. Default: configured backend value
variant         day or night. Default: day
```

Example:

```text
GET /api/status/fci/video-snapshot?frame_index=300&use_cache=false
GET /api/status/fci/video-snapshot?variant=night&frame_index=300
GET /api/status/faie/video-snapshot?variant=night&frame_index=300
```

Example response:

```json
{
  "location_id": "fci",
  "total_slots": 75,
  "occupied_count": 61,
  "available_count": 14,
  "slots": [
    { "slot_id": "A1", "occupied": true }
  ],
  "source": {
    "type": "video_snapshot",
    "variant": "day",
    "video_path": "backend/app/data/videos/fci/fci_video.mov",
    "frame_index": 300,
    "cached": false
  }
}
```

## Video Sampled Status

```text
GET /api/status/{location_id}/video-samples
```

Purpose: sample multiple frames and return both per-frame results and a majority-vote summary.

Optional query parameters:

```text
sample_count    Number of frames to sample. Default: 5. Range: 1-20
start_frame     First frame to sample. Default: 0
frame_step      Number of frames between samples. Default: 30
threshold       Slot polygon overlap threshold
box_threshold   Detection-box overlap threshold
confidence      YOLO confidence threshold
image_size      YOLO inference image size
variant         day or night. Default: day
```

Example:

```text
GET /api/status/fci/video-samples?sample_count=5&start_frame=0&frame_step=30
```

## Debug Visualization

```text
GET /api/debug/{location_id}
```

Default purpose: generate a JPEG overlay for a video frame.

Optional query parameters:

```text
source          video or static. Default: video
frame_index     Used when source=video. Default: 0
threshold
box_threshold
confidence
image_size
variant         day or night. Default: day
```

Examples:

```text
GET /api/debug/fci?source=video&frame_index=300
GET /api/debug/fci?source=video&variant=night&frame_index=300
GET /api/debug/faie?source=video&variant=night&frame_index=300
GET /api/debug/faie?source=static
```

Debug image meaning:

```text
Blue boxes: YOLO vehicle detections
Red slot polygons: occupied slots
Green slot polygons: available slots
Sxx% label: slot-overlap percentage
Summary bar: location, slot counts, vehicle count, and active thresholds
```

Generated debug files are saved under:

```text
backend/app/data/outputs/
```

This folder is ignored by Git.
