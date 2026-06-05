# ParkViewRT Frontend

This folder contains the React dashboard for ParkViewRT. It displays the FCI
and FAIE parking layouts, plays local parking footage served by the backend,
and requests frame-synchronized parking status from the FastAPI API.

For the full project guide, start with the root `README.md`. This file is the
frontend-only quick reference.

## Stack

```text
React 18
Vite
TypeScript
Tailwind-style utility classes
Lucide icons
Radix UI / local ui components
```

## Install

From inside `frontend/`:

```powershell
npm install
```

## Run

Start the backend first on `127.0.0.1:8001`, then run:

```powershell
npm run dev
```

Open:

```text
http://localhost:5173/
http://localhost:5173/fci-parking
http://localhost:5173/faie-parking
```

## Build

```powershell
npm run build
```

The generated `dist/` folder is ignored by Git.

## Backend URL

The API base URL is configured in:

```text
frontend/config/env.ts
```

Current value:

```ts
export const API_BASE_URL = "http://127.0.0.1:8001";
```

If the backend runs on a different port, update this file before testing.

## Important Files

```text
index.html
main.tsx
vite.config.ts
config/env.ts
api/parkingApi.ts
hooks/useParkingStatus.ts
types/parking.ts
app/App.tsx
app/components/
styles/
assets/
```

`main.tsx`: React entry point.

`app/App.tsx`: route definitions for the home, FCI, and FAIE pages.

`config/env.ts`: backend URL used by all API calls.

`api/parkingApi.ts`: typed fetch helpers for backend endpoints.

`hooks/useParkingStatus.ts`: loads frame-0 status, syncs video playback to
backend frame snapshots, handles refresh, and provides demo-random status.

`types/parking.ts`: TypeScript DTOs for parking status, slot status, video
metadata, and sampled status.

`assets/mmu-logo.png`: MMU logo used in the dashboard.

`styles/`: global CSS files.

## Main Components

```text
app/components/HomePage.tsx
app/components/FCIParkingView.tsx
app/components/FAIEParkingView.tsx
app/components/ParkingSlot.tsx
app/components/ParkingVideoPreview.tsx
app/components/ui/
```

`HomePage.tsx`: landing page with navigation to FCI and FAIE dashboards.

`FCIParkingView.tsx`: FCI parking page. It provides the day/night selector,
status cards, detection debug link, FCI row-plan layout, occlusion count, and
video preview.

`FAIEParkingView.tsx`: FAIE parking page. It provides the day/night selector,
status cards, detection debug link, U-shaped FAIE layout, and video preview.

`ParkingSlot.tsx`: shared slot display component. It supports occupied,
available, occluded, and unmonitored states.

`ParkingVideoPreview.tsx`: video player. It loads backend video metadata,
plays the selected video variant, and reports frame changes to the dashboard.

`components/ui/`: reusable UI primitives. Most project-specific parking logic is
in the main components listed above, not in this folder.

## Frontend Flow

```text
Parking page opens
  -> useParkingStatus requests frame 0
  -> ParkingVideoPreview requests video metadata
  -> video plays from /api/video/{location_id}?variant=...
  -> currentTime * fps becomes frame_index
  -> useParkingStatus requests /api/status/{location_id}/video-snapshot
  -> dashboard slot colors update
```

The hook throttles sync requests with `MIN_SYNC_FRAME_DISTANCE` so the frontend
does not ask the backend to run YOLO on every tiny playback movement.

## Variant and Slot Display Rules

Both parking pages send `variant=day` or `variant=night` to the backend.

FCI display:

```text
Day:   A1-A78 monitored
Night: A1-A77 monitored, A78 displayed as unmonitored for layout consistency
```

FAIE display:

```text
Day:   B1-B40 displayed, B1-B16 and B24-B31 monitored
Night: B1-B40 displayed, B1-B15 and B24-B26 monitored
```

Important: frontend display slots are not the real occupancy source. Real
detection depends on runtime polygon files in:

```text
backend/app/data/slots/
```

## Debug Links

The `Detection Debug` button opens:

```text
/api/debug/{location_id}?source=video&variant={day|night}&frame_index={current_frame}
```

Use this image to confirm whether YOLO boxes and slot polygons match the video
frame being displayed.

## Common Issues

### Failed to fetch

Make sure the backend is running and `config/env.ts` points to the correct URL.

### Video is black

The backend may be serving an HEVC source video directly. Run the backend
browser-video preparation tool:

```powershell
py -3.11 backend/app/tools/prepare_browser_videos.py
```

Then refresh the browser.

### Slot count looks different from detection count

The dashboard may display unmonitored slots to preserve layout shape. Check the
backend runtime slot JSON files to see which slots are actually monitored.

### Status feels delayed during playback

Frame analysis runs YOLO on the backend, so it is intentionally throttled. Use
the Refresh button or Detection Debug link when checking a specific frame.

## Related Docs

```text
../README.md
../docs/api_contract.md
../docs/architecture.md
../docs/testing_plan.md
```
