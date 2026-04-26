# ParkViewRT Testing Plan

This document describes the current manual and planned automated testing approach for the ParkViewRT FYP2 implementation.

## Backend Manual Tests

Start backend:

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Health Endpoint

Open:

```text
http://127.0.0.1:8000/api/health
```

Expected:

```json
{
  "status": "ok",
  "model_loaded": true,
  "locations": ["fci", "faie"]
}
```

### FCI Status

Open:

```text
http://127.0.0.1:8000/api/status/fci
```

Expected current static-image result:

```text
total_slots: 8
occupied_count: 8
available_count: 0
```

### FAIE Status

Open:

```text
http://127.0.0.1:8000/api/status/faie
```

Expected current static-image result:

```text
total_slots: 8
occupied_count: 8
available_count: 0
```

### Debug Images

Open:

```text
http://127.0.0.1:8000/api/debug/fci
http://127.0.0.1:8000/api/debug/faie
```

Expected:

```text
JPEG image loads in browser
YOLO car detections are drawn in blue
Slot polygons are drawn red or green
Summary bar shows counts and thresholds
Current FCI and FAIE target slots show occupied
```

### Video Snapshot

Place a video under:

```text
backend/app/data/videos/fci/
backend/app/data/videos/faie/
```

Open:

```text
http://127.0.0.1:8000/api/status/fci/video-snapshot
```

Optional frame selection:

```text
http://127.0.0.1:8000/api/status/fci/video-snapshot?frame_index=10
```

Expected:

```text
JSON response contains normal parking counts
JSON response includes source.type = video_snapshot
JSON response includes selected frame_index
```

### Multi-Frame Video Samples

Place a video under:

```text
backend/app/data/videos/fci/
backend/app/data/videos/faie/
```

Open:

```text
http://127.0.0.1:8000/api/status/fci/video-samples?sample_count=5&start_frame=0&frame_step=30
```

Expected:

```text
JSON response includes source.type = video_samples
source.frame_indices lists the sampled frame numbers
samples contains one occupancy result per sampled frame
summary contains majority-vote occupancy per slot
summary.sample_count matches the number of processed frames
```

### Threshold Tuning Tests

Use query parameters to compare output:

```text
/api/debug/fci?threshold=0.30&confidence=0.20&image_size=1600
/api/debug/faie?threshold=0.30&confidence=0.20&image_size=1600
```

Lower confidence may detect more cars but can increase false positives. Larger image sizes improve small vehicle detection but increase processing time.

## Frontend Manual Tests

Start frontend:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173/fci-parking
http://localhost:5173/faie-parking
```

Expected:

```text
Page loads without console errors
Available and occupied counts match backend
Refresh button reloads backend status
Last updated timestamp changes after refresh
Detection Debug opens the backend debug image in a new tab
```

## Build Verification

Run:

```powershell
cd frontend
npm run build
```

Expected:

```text
Vite build completes successfully
No TypeScript or import errors
```

Backend syntax check:

```powershell
py -3.11 -c "import ast, pathlib; [ast.parse(path.read_text(encoding='utf-8')) for path in pathlib.Path('backend/app').rglob('*.py')]; print('syntax ok')"
```

Expected:

```text
syntax ok
```

## Planned Automated Tests

Backend tests to add:

```text
GET /api/health returns status ok: done
GET /api/status/fci returns expected response fields: done
GET /api/status/faie accepts tuning query params: done
invalid location returns 404: done
debug endpoint returns image/jpeg: done
video snapshot endpoint returns status JSON: done
video samples endpoint returns aggregated status JSON: done
```

Frontend tests are not required yet, but future checks can verify that:

```text
parking pages render
refresh button calls the API
last updated text appears after successful fetch
debug link points to the correct backend URL
```

## Known Testing Risks

```text
Results depend on pretrained YOLO behavior.
Results may change if model weights or image resolution settings change.
Real video testing may require different thresholds from static image testing.
Camera angle, shadows, trees, and occlusions can affect detection accuracy.
```
