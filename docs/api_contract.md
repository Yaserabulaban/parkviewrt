# ParkViewRT API Contract

Base URL during local development:

```text
http://127.0.0.1:8000
```

The active backend implementation is under `backend/app`.

## Health Check

```text
GET /api/health
```

Purpose: confirm that the FastAPI backend is running and that the YOLO detector object is available.

Example response:

```json
{
  "status": "ok",
  "model_loaded": true,
  "locations": ["fci", "faie"]
}
```

## Parking Status

```text
GET /api/status/{location_id}
```

Supported `location_id` values:

```text
fci
faie
```

Purpose: run pretrained YOLO on the current static image for the selected location, compare detected car boxes with slot polygons, and return occupancy counts.

Optional query parameters:

```text
threshold      Slot polygon overlap threshold. Default: 0.30
box_threshold  Detection-box overlap threshold. Default: 0.20
confidence     YOLO confidence threshold. Default: 0.20
image_size     YOLO inference image size. Default: 1600
```

Example:

```text
GET /api/status/fci?threshold=0.30&confidence=0.20&image_size=1600
```

Example response:

```json
{
  "location_id": "fci",
  "total_slots": 8,
  "occupied_count": 8,
  "available_count": 0,
  "slots": [
    { "slot_id": "A1", "occupied": true },
    { "slot_id": "A2", "occupied": true }
  ]
}
```

Error cases:

```json
{
  "detail": "Unknown location: example"
}
```

```json
{
  "detail": "Parking image not found for location: fci"
}
```

## Debug Visualization

```text
GET /api/debug/{location_id}
```

Purpose: generate and return a JPEG image showing YOLO detections and slot occupancy decisions.

Optional query parameters are the same as `/api/status/{location_id}`:

```text
threshold
box_threshold
confidence
image_size
```

Example:

```text
GET /api/debug/faie?confidence=0.20&image_size=1600
```

Output: `image/jpeg`

Debug image meaning:

```text
Blue boxes: YOLO car detections
Red slot polygons: occupied slots
Green slot polygons: available slots
Sxx% label: slot-overlap percentage
Top summary bar: location, slot counts, detection count, and active thresholds
```

Generated debug files are saved locally under:

```text
backend/app/data/outputs/
```

This folder is ignored by Git.
