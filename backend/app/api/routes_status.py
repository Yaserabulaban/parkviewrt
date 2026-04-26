from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.services.occupancy_service import OccupancyService

router = APIRouter()
occupancy_service = OccupancyService()


@router.get("/status/{location_id}")
def get_real_status(location_id: str):
    if location_id not in {"fci", "faie"}:
        raise HTTPException(status_code=404, detail="Unknown location")

    base_dir = Path(__file__).resolve().parent.parent
    video_dir = base_dir / "data" / "videos" / location_id

    video_files = list(video_dir.glob("*.mp4"))
    if not video_files:
        raise HTTPException(status_code=404, detail="No video found for this location")

    video_path = str(video_files[0])

    return occupancy_service.process_video(location_id, video_path)