from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.parking import ParkingStatusResponse
from app.settings import get_settings
from app.services.occupancy import ParkingOccupancyService
from app.services.video_snapshot import VideoSnapshotService


router = APIRouter(prefix="/api", tags=["parking-status"])
settings = get_settings()
occupancy_service = ParkingOccupancyService()
video_snapshot_service = VideoSnapshotService(occupancy_service)


@router.get("/health")
def get_health_status():
    return {
        "status": "ok",
        "model_loaded": hasattr(occupancy_service.detector, "model"),
        "locations": ["fci", "faie"],
    }


@router.get("/config")
def get_backend_config():
    return {
        "detection": settings.detection.as_dict(),
        "locations": ["fci", "faie"],
    }


@router.get("/status/{location_id}", response_model=ParkingStatusResponse)
def get_parking_status(
    location_id: str,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    try:
        return occupancy_service.get_status(
            location_id,
            overlap_threshold=threshold,
            box_overlap_threshold=box_threshold,
            confidence_threshold=confidence,
            image_size=image_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/status/{location_id}/video-snapshot")
def get_video_snapshot_status(
    location_id: str,
    frame_index: int = 0,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    try:
        return video_snapshot_service.get_snapshot_status(
            location_id,
            frame_index=frame_index,
            overlap_threshold=threshold,
            box_overlap_threshold=box_threshold,
            confidence_threshold=confidence,
            image_size=image_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/status/{location_id}/video-samples")
def get_video_sampled_status(
    location_id: str,
    sample_count: int = 5,
    start_frame: int = 0,
    frame_step: int = 30,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    try:
        return video_snapshot_service.get_sampled_status(
            location_id,
            sample_count=sample_count,
            start_frame=start_frame,
            frame_step=frame_step,
            overlap_threshold=threshold,
            box_overlap_threshold=box_threshold,
            confidence_threshold=confidence,
            image_size=image_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/debug/{location_id}")
def get_debug_visualization(
    location_id: str,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    try:
        image_path = occupancy_service.create_debug_image(
            location_id,
            overlap_threshold=threshold,
            box_overlap_threshold=box_threshold,
            confidence_threshold=confidence,
            image_size=image_size,
        )
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            filename=f"{location_id.lower()}_debug.jpg",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
