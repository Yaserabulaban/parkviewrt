from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.parking import ParkingStatusResponse
from app.services.occupancy import ParkingOccupancyService


router = APIRouter(prefix="/api", tags=["parking-status"])
occupancy_service = ParkingOccupancyService()


@router.get("/health")
def get_health_status():
    return {
        "status": "ok",
        "model_loaded": hasattr(occupancy_service.detector, "model"),
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
