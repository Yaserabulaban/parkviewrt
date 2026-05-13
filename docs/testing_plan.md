# ParkViewRT Testing Plan

This document describes the current manual and automated testing flow for the video-based ParkViewRT dashboard.

## Backend Setup

Install dependencies:

```powershell
py -3.11 -m pip install -r backend/requirements.txt
```

Start backend on the port used by the frontend:

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

If port `8001` is unavailable, run on another port and update `frontend/config/env.ts`.

## Video Placement

Place local videos under:

```text
backend/app/data/videos/fci/
backend/app/data/videos/faie/
```

Recommended filenames:

```text
fci/day/fci_video.mov
fci/night/fci_video.mov
faie/day/faie_video.MOV
faie/night/faie_video.MOV
```

For FCI and FAIE, the dashboard sends `variant=day` or `variant=night`; the backend prefers videos under the matching variant folder. Supported extensions are `.mp4`, `.avi`, `.mov`, and `.mkv`.

After replacing a video with the same filename, clear generated frame status cache if needed:

```powershell
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/fci
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/faie
```

The dashboard video itself uses cache-busting metadata, so the browser should load the new file after a refresh.

## Backend Manual Tests

Health:

```text
http://127.0.0.1:8001/api/health
```

Config:

```text
http://127.0.0.1:8001/api/config
```

Expected slot metadata:

```text
FCI day display slots: 77, monitored slots: 75
FCI night monitored slots: 77
FAIE day display slots: 40, monitored slots: 22
FAIE night display slots: 40, monitored slots: 18
```

Video metadata:

```text
http://127.0.0.1:8001/api/video/fci/metadata?variant=day
http://127.0.0.1:8001/api/video/fci/metadata?variant=night
http://127.0.0.1:8001/api/video/faie/metadata?variant=day
http://127.0.0.1:8001/api/video/faie/metadata?variant=night
```

Expected:

```text
file_name matches the intended video
frame_count > 0
fps > 0
file_size and last_modified are present
```

Video snapshot:

```text
http://127.0.0.1:8001/api/status/fci/video-snapshot?variant=day&frame_index=0&use_cache=false
http://127.0.0.1:8001/api/status/fci/video-snapshot?variant=night&frame_index=0&use_cache=false
http://127.0.0.1:8001/api/status/faie/video-snapshot?variant=day&frame_index=0&use_cache=false
http://127.0.0.1:8001/api/status/faie/video-snapshot?variant=night&frame_index=0&use_cache=false
```

Expected:

```text
JSON response includes source.type = video_snapshot
source.frame_index matches the requested frame or the last valid frame
total_slots is 75 for FCI day, 77 for FCI night, 22 for FAIE day, and 18 for FAIE night
available_count + occupied_count = total_slots
```

Video debug:

```text
http://127.0.0.1:8001/api/debug/fci?source=video&variant=day&frame_index=0
http://127.0.0.1:8001/api/debug/fci?source=video&variant=night&frame_index=0
http://127.0.0.1:8001/api/debug/faie?source=video&variant=day&frame_index=0
http://127.0.0.1:8001/api/debug/faie?source=video&variant=night&frame_index=0
```

Expected:

```text
JPEG loads in browser
vehicle boxes are drawn in blue
slot polygons are red or green
summary bar shows thresholds and vehicle count
slot polygons align with the current video camera angle
```

Multi-frame samples:

```text
http://127.0.0.1:8001/api/status/fci/video-samples?variant=day&sample_count=5&start_frame=0&frame_step=30
```

Expected:

```text
source.type = video_samples
source.frame_indices lists sampled frames
samples contains one status result per frame
summary contains majority-vote occupancy per slot
```

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
page loads without console errors
video preview shows the intended local video
initial status comes from video frame 0
playing the video updates the dashboard status as frame sync requests complete
Refresh reloads video frame 0
Video Snapshot samples the current reported frame
Video Samples loads the majority-vote summary
Detection Debug opens the current video-frame overlay
Demo Random still works without video analysis
```

## Automated Checks

Backend tests:

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m pytest backend/app/tests
```

Frontend build:

```powershell
cd frontend
npm run build
```

Optional backend syntax check:

```powershell
py -3.11 -c "import ast, pathlib; [ast.parse(path.read_text(encoding='utf-8')) for path in pathlib.Path('backend/app').rglob('*.py')]; print('syntax ok')"
```

## Known Testing Risks

```text
Results depend on pretrained YOLO behavior.
Camera angle changes require regenerated slot polygons.
Video frame analysis may lag playback on slower machines.
Tree cover, shadows, and occlusion can reduce vehicle detection accuracy.
Cached frame results can become stale when a video is replaced with the same filename.
```
