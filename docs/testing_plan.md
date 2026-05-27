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

For dashboard playback, prefer H.264 `.mp4` copies of local recordings. If a
video frame can be extracted by OpenCV but its dashboard preview is black, the
recording may be using a browser-incompatible HEVC profile and should be
transcoded to H.264 `.mp4`. Prepare a consistent browser copy for each day and
night recording with:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

The preview endpoint selects each `*_browser.mp4` copy; snapshot and debug
endpoints continue reading the matching original annotation recording.
Existing current H.264 browser copies are reused rather than transcoded again.

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
FCI day display slots: 78, monitored slots: 78
FCI night monitored slots: 77
FAIE day display slots: 40, monitored slots: 24 (`B1-B16`, `B24-B31`)
FAIE night display slots: 40, monitored slots: 18 (`B1-B15`, `B24-B26`)
FCI day visual numbering runs left-to-right within each visible lane: `A1-A6`, `A7-A25`, `A26-A47`, `A48-A65`, `A66-A78`
FAIE visual numbering: main curb `B1-B17`, angled spaces `B18-B23`, final row `B24-B40` from right to left
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
total_slots is 78 for FCI day, 77 for FCI night, 24 for FAIE day, and 18 for FAIE night
available_count + occupied_count + occluded_count = total_slots
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
known occluded FCI day slots can be amber
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
Detection Debug opens the current video-frame overlay
Demo Random still works without video analysis
Video snapshot and multi-frame sample endpoints remain available for backend testing
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
