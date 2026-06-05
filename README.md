# ParkViewRT

ParkViewRT is a video-based parking slot monitoring dashboard for the MMU FCI
and FAIE parking areas. The system plays local parking videos in the browser,
samples matching video frames in the backend, runs YOLO vehicle detection, and
compares the detected vehicles with manually labeled parking-slot polygons.

The current FYP2 implementation is focused on:

- FCI and FAIE day/night video variants.
- YOLO-based occupied, available, and occluded slot status.
- Runtime polygon JSON files generated from annotation exports.
- Debug overlays for checking detections against parking-slot labels.
- Local browser-safe H.264 playback copies for recordings that browsers cannot
  decode directly.

## Quick Start

Run these commands from the repository root unless a command says otherwise.

### 1. Backend Setup

```powershell
py -3.11 -m pip install -r backend/requirements.txt
```

Model weights are expected under:

```text
backend/app/models/yolo11n.pt
```

The model files are ignored by Git. If the file is missing and the machine has
network access, Ultralytics may download the model automatically.

### 2. Video Placement

Place the local videos in these folders:

```text
backend/app/data/videos/fci/day/fci_video.mov
backend/app/data/videos/fci/night/fci_video.mov
backend/app/data/videos/faie/day/faie_video.MOV
backend/app/data/videos/faie/night/faie_video.MOV
```

Videos are ignored by Git because they are large local files.

### 3. Prepare Browser Playback Copies

Some phone recordings use HEVC. OpenCV can still read those videos for
detection, but browsers may show a black video preview. Generate H.264 browser
copies with:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

This creates local `*_browser.mp4` files beside the source videos. The backend
uses original recordings for detection and debug overlays, while the dashboard
video preview uses the browser copies when they exist.

### 4. Start Backend

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 5. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
http://localhost:5173/fci-parking
http://localhost:5173/faie-parking
```

## Common Commands

Backend tests:

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m pytest backend/app/tests
```

Frontend production build:

```powershell
cd frontend
npm run build
```

Generate runtime slot JSON files from annotation exports:

```powershell
py -3.11 backend/app/tools/generate_fci_slots.py
py -3.11 backend/app/tools/generate_faie_slots.py
```

Precompute video frame status cache for repeated testing:

```powershell
$env:PYTHONPATH='backend'
py -3.11 backend/app/tools/cache_video_status.py fci --variant day
```

## Repository Structure

```text
.
  .env.example
  .gitignore
  README.md
  backend/
  colab/
  docs/
  frontend/
```

### Root Files

`README.md`: this project guide.

`.env.example`: optional backend detection settings for overriding defaults in
the local environment.

`.gitignore`: keeps generated outputs, local videos, model weights, virtual
environments, and frontend build folders out of Git.

`1221305612_Md.ZubairHassanTarif_FYP1_Report.pdf`: prior FYP report artifact.
It is not used by the runtime application.

## Backend Folder

```text
backend/
  README.md
  requirements.txt
  app/
```

`backend/requirements.txt`: Python dependencies for FastAPI, Ultralytics,
OpenCV, Shapely, tests, and browser-video preparation.

`backend/README.md`: backend-only quick reference.

### Backend App Files

```text
backend/app/
  main.py
  settings.py
  api/routes/status.py
  schemas/parking.py
  services/
  tools/
  tests/
  data/
  models/
```

`main.py`: creates the FastAPI app and configures CORS for the frontend.

`settings.py`: reads detection settings from environment variables and applies
validation for thresholds, image size, and model path.

`api/routes/status.py`: defines the HTTP API used by the dashboard:
configuration, demo status, video snapshot status, video metadata, video file
serving, debug images, and multi-frame samples.

`schemas/parking.py`: Pydantic response models for parking status payloads.

### Backend Services

```text
backend/app/services/
  occupancy.py
  video_snapshot.py
  yolo_detector.py
  slot_layouts.py
```

`occupancy.py`: core parking analysis service. It loads slot polygons, runs YOLO,
calculates polygon/detection overlap, applies known occlusion rules, and creates
debug images.

`video_snapshot.py`: video-frame service. It selects original source videos for
detection, selects `*_browser.mp4` files for preview playback, reads requested
frames, writes frame-status cache files, and builds sampled multi-frame
summaries.

`yolo_detector.py`: small wrapper around Ultralytics YOLO. It filters detections
to vehicle classes used by this project.

`slot_layouts.py`: display metadata used by the frontend/demo mode. This is not
the source of real occupancy polygons; real detection depends on the runtime
slot JSON files under `backend/app/data/slots/`.

### Backend Tools

```text
backend/app/tools/
  generate_fci_slots.py
  generate_faie_slots.py
  slot_generation.py
  prepare_browser_videos.py
  cache_video_status.py
  visualize_slots.py
```

`generate_fci_slots.py`: maps FCI annotation-export polygon IDs into runtime
`A` slot order for day and night.

`generate_faie_slots.py`: maps FAIE annotation exports into runtime `B` slot
IDs. FAIE shows `B1-B40` on the dashboard, but only visible monitored slots are
included in runtime JSON.

`slot_generation.py`: shared helper used by both slot generators. It validates
annotation ordering and writes normalized runtime slot JSON.

`prepare_browser_videos.py`: creates H.264 `*_browser.mp4` files for reliable
browser playback without changing the original videos used for detection.

`cache_video_status.py`: optional helper for precomputing video-frame status
results.

`visualize_slots.py`: utility for drawing slot polygons on reference images.

### Backend Data

```text
backend/app/data/
  images/
  slots/
  videos/      ignored by Git
  outputs/     ignored by Git
```

`images/`: tracked static reference images for FCI and FAIE day/night.

`slots/`: tracked annotation exports and runtime slot JSON files. Files ending
in `_annotations.json` are source exports. Files ending in `_slots.json` are the
runtime polygons used by detection.

`videos/`: ignored local parking videos and generated browser playback copies.

`outputs/`: ignored debug images and video status cache.

### Backend Models

```text
backend/app/models/
```

Model weights such as `yolo11n.pt` live here locally and are ignored by Git.

## Frontend Folder

```text
frontend/
  package.json
  vite.config.ts
  config/env.ts
  api/parkingApi.ts
  hooks/useParkingStatus.ts
  app/
  styles/
  types/
```

`package.json`: frontend dependencies and scripts.

`frontend/README.md`: frontend-only quick reference for dashboard setup,
structure, API wiring, and troubleshooting.

`vite.config.ts`: Vite configuration and `@` path alias.

`config/env.ts`: backend API base URL. It currently points to
`http://127.0.0.1:8001`.

`api/parkingApi.ts`: typed fetch helpers for backend API endpoints.

`hooks/useParkingStatus.ts`: React hook that loads frame-0 status, syncs video
playback to backend frame snapshots, handles refresh, and provides demo status.

### Frontend App Files

```text
frontend/app/
  App.tsx
  components/
```

`App.tsx`: route definitions for the home, FCI, and FAIE pages.

`components/HomePage.tsx`: landing/navigation page.

`components/FCIParkingView.tsx`: FCI dashboard, day/night selector, FCI row
layout, occlusion count, debug link, and video preview.

`components/FAIEParkingView.tsx`: FAIE dashboard, day/night selector, U-shaped
layout, debug link, and video preview.

`components/ParkingVideoPreview.tsx`: video player that reads backend metadata,
plays the selected video, and reports frame changes for synchronized analysis.

`components/ParkingSlot.tsx`: reusable slot component for occupied, available,
occluded, and unmonitored display states.

`components/ui/`: reusable UI primitives generated for the React interface.
Most project-specific dashboard logic is outside this folder.

### Frontend Types and Styles

`types/parking.ts`: TypeScript DTOs shared by frontend API calls and components.

`styles/`: global styling files.

## Docs Folder

```text
docs/
  api_contract.md
  architecture.md
  dataset_plan.md
  testing_plan.md
  model_evaluation.md
```

`api_contract.md`: endpoint behavior and response examples.

`architecture.md`: runtime flow, occupancy rules, slot coverage, video/cache
behavior, and current limitations.

`dataset_plan.md`: data layout, slot JSON format, capture requirements, and
future dataset notes.

`testing_plan.md`: manual and automated validation checklist.

`model_evaluation.md`: current model comparison notes for report writing.

## Colab Folder

```text
colab/
  README.md
  evaluate_models.py
  evaluate_model_accuracy.py
  tune_thresholds.py
  generate_evaluation_report.py
  ground_truth/
```

The Colab area is for reproducible model comparison, verified accuracy testing,
and threshold tuning. Generated CSV files and debug images are written under
`colab/outputs/`, which is ignored by Git. The reviewed validation labels are
kept under `colab/ground_truth/` so the evaluation can be rerun after generated
outputs are cleaned.

## Runtime Workflow

The dashboard workflow is:

```text
browser video time
  -> frontend frame index
  -> /api/status/{location_id}/video-snapshot
  -> OpenCV reads original source video frame
  -> YOLO detects vehicles
  -> Shapely compares detections with slot polygons
  -> backend returns occupied/available/occluded slots
  -> React layout updates
```

The video preview workflow is separate:

```text
/api/video/{location_id}/metadata
  -> choose *_browser.mp4 when available
  -> browser plays H.264 MP4 preview
```

This separation is intentional. Browser copies solve playback compatibility
without changing the original source frames used for analysis.

## Slot JSON and Labeling Conventions

There are two slot file types:

```text
*_annotations.json  source polygon exports from labeling
*_slots.json        runtime polygons used by backend detection
```

Runtime slot JSON format:

```json
{
  "location_id": "fci",
  "layout_type": "video_day_frame",
  "slots": [
    {
      "slot_id": "A1",
      "row": "A",
      "shape": "polygon",
      "points": [[0, 0], [10, 0], [10, 10], [0, 10]]
    }
  ]
}
```

Important conventions:

- FCI slots use prefix `A`.
- FAIE slots use prefix `B`.
- Real detection only works for slots that exist in runtime `_slots.json` files.
- Dashboard display slots may include unmonitored slots to preserve the visual
  parking layout.
- Annotation export IDs are not always the same as displayed slot numbers. The
  generator scripts map source polygon IDs into the dashboard slot order.
- If a video camera angle changes, relabel the slots and regenerate the
  matching runtime JSON file.

Current slot coverage:

```text
FCI day: A1-A78, 78 monitored slots
FCI night: A1-A77, 77 monitored slots
FAIE day: B1-B40 displayed, B1-B16 and B24-B31 monitored
FAIE night: B1-B40 displayed, B1-B15 and B24-B26 monitored
```

## Cache and Generated Output

Frame status cache lives under:

```text
backend/app/data/outputs/video_status_cache/
```

Cache keys include:

- location and variant
- selected source video identity
- runtime slot file identity
- threshold and image-size settings
- frame index

Clear cache after replacing a video or slot file if stale results appear:

```powershell
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/fci
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/faie
```

Debug overlays are also written under:

```text
backend/app/data/outputs/
```

Keep useful debug images while validating the project, but do not commit this
folder.

## Detection Settings

Defaults are defined in `backend/app/settings.py`:

```text
PARKVIEWRT_MODEL_PATH=backend/app/models/yolo11n.pt
PARKVIEWRT_CONFIDENCE=0.20
PARKVIEWRT_IMAGE_SIZE=1600
PARKVIEWRT_SLOT_THRESHOLD=0.25
PARKVIEWRT_BOX_THRESHOLD=0.20
```

Use `.env.example` as a reference for environment variables. Threshold tuning is
complete for the current validation set, and the existing defaults are retained
because they achieved `591/591` correct verified slot labels.

## Evaluation Evidence

Model and threshold evidence is documented in:

```text
docs/model_evaluation.md
```

Current selected values:

```text
YOLO model: yolo11n.pt
Confidence threshold: 0.20
Slot overlap threshold: 0.25
Box overlap threshold: 0.20
```

The verified validation set contains 12 video frames and 591 slot-status labels
under:

```text
colab/ground_truth/slot_status_ground_truth.csv
```

## Troubleshooting

### Backend import errors

Set `PYTHONPATH` before running backend commands:

```powershell
$env:PYTHONPATH='backend'
```

### Dashboard cannot fetch status

Check that the backend is running on `127.0.0.1:8001` and that
`frontend/config/env.ts` points to the same URL.

### Video preview is black

The source video may be HEVC. Generate H.264 browser copies:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

Then refresh the dashboard.

### Debug image polygons do not align with cars

The camera angle likely changed after labeling. Extract a new stable frame,
relabel the affected variant, regenerate runtime slot JSON, and clear cache.

### Results look stale after replacing a video

Clear the matching video status cache:

```powershell
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/fci
Remove-Item -Recurse -Force backend/app/data/outputs/video_status_cache/faie
```

### A slot is displayed but never changes

It may be an unmonitored dashboard-only slot. Check the matching runtime
`*_slots.json`; real occupancy depends on polygons in that file, not only on
the frontend display layout.

### YOLO misses a car under trees or shadows

Use the debug endpoint to confirm whether YOLO detected the vehicle. Known FCI
day tree-covered spaces can be marked `occluded`, but the remaining improvement
path is threshold tuning, model comparison, or a custom dataset.

### Frontend build artifacts appear

`frontend/dist/` is generated and ignored by Git. Rebuild it with:

```powershell
cd frontend
npm run build
```

## Useful API URLs

```text
http://127.0.0.1:8001/api/health
http://127.0.0.1:8001/api/config
http://127.0.0.1:8001/api/video/fci/metadata?variant=day
http://127.0.0.1:8001/api/status/fci/video-snapshot?variant=day&frame_index=0&use_cache=false
http://127.0.0.1:8001/api/debug/fci?source=video&variant=day&frame_index=0
```

Replace `fci` with `faie` and `day` with `night` as needed.

## Current Remaining Work

- Write the final FYP2 report using `docs/model_evaluation.md`,
  `docs/architecture.md`, and `docs/testing_plan.md` as source material.
- During the final demo, run the dashboard manually for FCI day, FCI night,
  FAIE day, and FAIE night to confirm browser playback and debug overlays.
- If any final video is retaken or relabeled, regenerate the matching runtime
  slot JSON and rerun model accuracy plus threshold tuning.
- Add deployment notes only if the project moves beyond local FastAPI/Vite
  execution.
