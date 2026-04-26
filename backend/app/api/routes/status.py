from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.parking import ParkingStatusResponse
from app.services.occupancy import ParkingOccupancyService


router = APIRouter(prefix="/api", tags=["parking-status"])
occupancy_service = ParkingOccupancyService()


@router.get("/status/{location_id}", response_model=ParkingStatusResponse)
def get_parking_status(location_id: str):
    try:
        return occupancy_service.get_status(location_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/debug/{location_id}")
def get_debug_visualization(location_id: str):
    try:
        image_path = occupancy_service.create_debug_image(location_id)
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            filename=f"{location_id.lower()}_debug.jpg",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
