# ParkViewRT Backend

FastAPI backend for the ParkViewRT occupancy detection pipeline.

## Setup

```powershell
cd backend
py -3.11 -m pip install -r requirements.txt
```

## Run

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Test

```powershell
$env:PYTHONPATH='backend'
py -3.11 -m pytest backend/app/tests
```

The backend expects model weights under `backend/app/models/` and real videos under
`backend/app/data/videos/{location_id}/`. Both are ignored by Git.
