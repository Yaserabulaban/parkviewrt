# ParkViewRT Backend

FastAPI backend for the ParkViewRT occupancy detection pipeline.

## Setup

```powershell
cd backend
py -3.11 -m pip install -r requirements.txt
```

## Run

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The frontend currently points to `http://127.0.0.1:8001` in `frontend/config/env.ts`.

## Test

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m pytest backend/app/tests
```

The backend expects model weights under `backend/app/models/` and local videos under `backend/app/data/videos/{location_id}/`. Both are ignored by Git.

Generated debug images, logs, and frame status cache are written under `backend/app/data/outputs/`, which is also ignored by Git.

## Browser Video Copies

The detection pipeline reads the original local videos. The backend dependency
install includes FFmpeg support for preparing H.264 MP4 copies for reliable
dashboard video playback:

```powershell
py -3.11 app/tools/prepare_browser_videos.py
```

The generated `*_browser.mp4` files remain local under `app/data/videos/`.
Current H.264 playback files are reused, so the slow HEVC transcode only runs
when a source recording is replaced or has no compatible playback copy.
