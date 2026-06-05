# ParkViewRT Backend

This folder contains the FastAPI backend for ParkViewRT. It reads local FCI and
FAIE parking videos, samples frames with OpenCV, runs YOLO vehicle detection,
compares detections with runtime slot polygons, and returns parking status to
the React dashboard.

For the full project guide, start with the root `README.md`. This file is the
backend-only quick reference.

## Stack

```text
FastAPI
Python 3.11
OpenCV
Ultralytics YOLO
Shapely
imageio-ffmpeg
pytest
```

## Install

From the repository root:

```powershell
py -3.11 -m pip install -r backend/requirements.txt
```

Or from inside `backend/`:

```powershell
py -3.11 -m pip install -r requirements.txt
```

## Run

From the repository root:

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The frontend API base URL is configured in:

```text
frontend/config/env.ts
```

It currently points to:

```text
http://127.0.0.1:8001
```

## Test

From the repository root:

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m pytest backend/app/tests
```

Optional syntax check:

```powershell
py -3.11 -m py_compile backend/app/services/occupancy.py backend/app/services/video_snapshot.py
```

## Required Local Files

Model weights are expected at:

```text
backend/app/models/yolo11n.pt
```

Model files are ignored by Git. If the file is missing and network access is
available, Ultralytics may download it automatically.

Local videos are expected under day/night variant folders:

```text
backend/app/data/videos/fci/day/fci_video.mov
backend/app/data/videos/fci/night/fci_video.mov
backend/app/data/videos/faie/day/faie_video.MOV
backend/app/data/videos/faie/night/faie_video.MOV
```

The video folder is ignored by Git.

## Browser Video Copies

Detection and debug endpoints read the original local videos so the analyzed
frames match the slot labels. The browser preview can use generated H.264
copies because some HEVC phone videos appear as a black screen in the browser.

Prepare playback copies from the repository root:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

This creates local files such as:

```text
backend/app/data/videos/fci/night/fci_video_browser.mp4
backend/app/data/videos/faie/night/faie_video_browser.mp4
```

Existing current H.264 browser copies are reused. HEVC sources are transcoded
only when no compatible copy exists or the source video is newer.

## Important Files

```text
app/main.py
app/settings.py
app/api/routes/status.py
app/schemas/parking.py
app/services/occupancy.py
app/services/video_snapshot.py
app/services/yolo_detector.py
app/services/slot_layouts.py
app/tools/
app/data/
app/models/
app/tests/
```

`app/main.py`: creates the FastAPI app and CORS configuration.

`app/settings.py`: loads detection settings from environment variables.

`app/api/routes/status.py`: exposes health, config, status, demo status, video
metadata, video file, debug image, and sampled video endpoints.

`app/schemas/parking.py`: response models for parking status.

`app/services/occupancy.py`: core YOLO and slot-overlap analysis.

`app/services/video_snapshot.py`: video-frame reading, frame cache, sampled
status, and source-vs-browser-playback video selection.

`app/services/yolo_detector.py`: Ultralytics YOLO wrapper filtered to vehicle
classes.

`app/services/slot_layouts.py`: frontend/demo display metadata. Real occupancy
polygons come from runtime JSON files in `app/data/slots/`.

## Data Files

Tracked reference images:

```text
app/data/images/fci_day.png
app/data/images/fci_night.png
app/data/images/faie_day.png
app/data/images/faie_night.png
```

Tracked slot files:

```text
app/data/slots/fci_day_annotations.json
app/data/slots/fci_day_slots.json
app/data/slots/fci_night_annotations.json
app/data/slots/fci_night_slots.json
app/data/slots/faie_day_annotations.json
app/data/slots/faie_day_slots.json
app/data/slots/faie_night_annotations.json
app/data/slots/faie_night_slots.json
```

`*_annotations.json` files are labeling exports.

`*_slots.json` files are runtime polygons used by the backend.

## Slot Coverage

```text
FCI day: A1-A78, 78 monitored slots
FCI night: A1-A77, 77 monitored slots
FAIE day: B1-B40 displayed, B1-B16 and B24-B31 monitored
FAIE night: B1-B40 displayed, B1-B15 and B24-B26 monitored
```

Dashboard display slots can include unmonitored spaces for layout consistency.
Real detection only happens for slots present in the matching runtime
`*_slots.json` file.

## Backend Tools

Generate runtime slot JSON from annotation exports:

```powershell
py -3.11 backend/app/tools/generate_fci_slots.py
py -3.11 backend/app/tools/generate_faie_slots.py
```

Prepare H.264 browser video copies:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

Precompute frame status cache:

```powershell
$env:PYTHONPATH='backend'
py -3.11 backend/app/tools/cache_video_status.py fci --variant day --max-frames 10
py -3.11 backend/app/tools/cache_video_status.py faie --variant night --max-frames 10
```

Draw slot previews on reference images:

```powershell
py -3.11 backend/app/tools/visualize_slots.py
```

## Environment Variables

Defaults are defined in `app/settings.py`:

```text
PARKVIEWRT_MODEL_PATH=backend/app/models/yolo11n.pt
PARKVIEWRT_CONFIDENCE=0.20
PARKVIEWRT_IMAGE_SIZE=1600
PARKVIEWRT_SLOT_THRESHOLD=0.25
PARKVIEWRT_BOX_THRESHOLD=0.20
```

Use the root `.env.example` as a reference. The app reads environment variables
from the shell; it does not automatically load `.env` files.

## Useful API URLs

```text
http://127.0.0.1:8001/api/health
http://127.0.0.1:8001/api/config
http://127.0.0.1:8001/api/video/fci/metadata?variant=day
http://127.0.0.1:8001/api/status/fci/video-snapshot?variant=day&frame_index=0&use_cache=false
http://127.0.0.1:8001/api/debug/fci?source=video&variant=day&frame_index=0
```

Replace `fci` with `faie` and `day` with `night` when testing other variants.

## Cache and Generated Outputs

Generated backend outputs are ignored by Git:

```text
app/data/outputs/
app/data/outputs/video_status_cache/
```

Clear cache after replacing a video or changing slot polygons if stale results
appear:

```powershell
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/fci
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/faie
```

Debug images are saved under `app/data/outputs/` and are useful for validation,
but they should not be committed.

## Troubleshooting

If imports fail, make sure `PYTHONPATH` is set:

```powershell
$env:PYTHONPATH='backend'
```

If the dashboard video is black but debug frames work, generate browser copies:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

If polygons do not align with vehicles, the camera angle changed. Relabel the
affected variant, regenerate runtime slot JSON, and clear the frame cache.

If a displayed slot never changes, check the matching runtime `*_slots.json`.
Frontend display slots are not the same thing as monitored detection polygons.
