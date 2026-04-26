from typing import List, Literal, Optional
from pydantic import BaseModel


class ParkingSlotDto(BaseModel):
    slot_id: str
    occupied: bool


class ParkingStatusResponse(BaseModel):
    location_id: Literal["fci", "faie"]
    total_slots: int
    occupied_count: int
    available_count: int
    slots: List[ParkingSlotDto]
    updated_at: Optional[str] = None