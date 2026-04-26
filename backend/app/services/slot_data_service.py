import json
from pathlib import Path


class SlotDataService:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        self.slots_dir = base_dir / "data" / "slots"

    def load_slots(self, location_id: str) -> dict:
        file_path = self.slots_dir / f"{location_id}_slots.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Slot file not found for location: {location_id}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)