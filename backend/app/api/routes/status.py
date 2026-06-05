from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.parking import ParkingStatusResponse
from app.settings import get_settings
from app.services.occupancy import ParkingOccupancyService
from app.services.slot_layouts import PARKING_SLOT_LAYOUTS, build_demo_parking_status
from app.services.video_snapshot import VideoSnapshotService


router = APIRouter(prefix="/api", tags=["parking-status"])
settings = get_settings()
occupancy_service = ParkingOccupancyService()
video_snapshot_service = VideoSnapshotService(occupancy_service)

VIDEO_MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
}


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
        "slot_layouts": PARKING_SLOT_LAYOUTS,
    }


@router.get("/status/{location_id}", response_model=ParkingStatusResponse)
def get_parking_status(
    location_id: str,
    variant: str | None = None,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    try:
        return occupancy_service.get_status(
            location_id,
            variant=variant,
            overlap_threshold=threshold,
            box_overlap_threshold=box_threshold,
            confidence_threshold=confidence,
            image_size=image_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/status/{location_id}/demo", response_model=ParkingStatusResponse)
def get_demo_parking_status(
    location_id: str,
    variant: str | None = None,
    occupancy_rate: float = 0.5,
    seed: int | None = None,
):
    try:
        return build_demo_parking_status(
            location_id,
            variant=variant,
            occupancy_rate=occupancy_rate,
            seed=seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status/{location_id}/video-snapshot")
def get_video_snapshot_status(
    location_id: str,
    variant: str | None = None,
    frame_index: int = 0,
    debug: bool = False,
    use_cache: bool = True,
    save_result: bool = True,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    # This is the dashboard's main live-analysis endpoint. The frontend sends
    # the current video frame index, and the backend analyzes that exact source
    # frame so the displayed video and occupancy state stay aligned.
    try:
        return video_snapshot_service.get_snapshot_status(
            location_id,
            variant=variant,
            frame_index=frame_index,
            include_debug_image=debug,
            use_cache=use_cache,
            save_result=save_result,
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
    variant: str | None = None,
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
            variant=variant,
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


@router.get("/video/{location_id}/metadata")
def get_parking_video_metadata(location_id: str, variant: str | None = None):
    # Metadata is based on the browser-playback file when available. That keeps
    # frontend frame-index calculations tied to the displayed video element.
    try:
        return video_snapshot_service.get_video_metadata(location_id, variant=variant)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/video/{location_id}")
def get_parking_video(location_id: str, variant: str | None = None):
    try:
        video_path = video_snapshot_service.get_video_path(location_id, variant=variant)
        return FileResponse(
            video_path,
            media_type=VIDEO_MEDIA_TYPES.get(video_path.suffix.lower(), "application/octet-stream"),
            filename=video_path.name,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
            },
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/debug/{location_id}")
def get_debug_visualization(
    location_id: str,
    source: str = "video",
    variant: str | None = None,
    frame_index: int = 0,
    threshold: float | None = None,
    box_threshold: float | None = None,
    confidence: float | None = None,
    image_size: int | None = None,
):
    # Debug images are intentionally served as files instead of JSON so they can
    # be opened directly from the dashboard and used as visual evidence during
    # slot-label validation.
    try:
        if source == "static":
            image_path = occupancy_service.create_debug_image(
                location_id,
                variant=variant,
                overlap_threshold=threshold,
                box_overlap_threshold=box_threshold,
                confidence_threshold=confidence,
                image_size=image_size,
            )
            filename = f"{location_id.lower()}_debug.jpg"
        elif source == "video":
            image_path = video_snapshot_service.create_debug_snapshot_image(
                location_id,
                variant=variant,
                frame_index=frame_index,
                overlap_threshold=threshold,
                box_overlap_threshold=box_threshold,
                confidence_threshold=confidence,
                image_size=image_size,
            )
            variant_prefix = f"{variant}_" if variant else ""
            filename = f"{location_id.lower()}_{variant_prefix}video_frame_{frame_index}_debug.jpg"
        else:
            raise ValueError("source must be either static or video")

        return FileResponse(
            image_path,
            media_type="image/jpeg",
            filename=filename,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
            },
        )
    except ValueError as exc:
        status_code = 400 if "source must be" in str(exc) else 404
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
