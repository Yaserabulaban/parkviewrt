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
