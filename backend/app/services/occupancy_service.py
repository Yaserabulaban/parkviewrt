from pathlib import Path

from app.services.slot_data_service import SlotDataService
from app.services.video_reader import VideoReader
from app.services.frame_sampler import FrameSampler
from app.services.yolo_detector import get_yolo_detector
from app.services.slot_mapper import SlotMapper


class OccupancyService:
    def __init__(self):
        self.slot_service = SlotDataService()
        self.frame_sampler = FrameSampler(sample_every_n_frames=10)
        self.detector = get_yolo_detector()
        self.mapper = SlotMapper(overlap_threshold=0.20)

    def process_video(self, location_id: str, video_path: str) -> dict:
        slot_data = self.slot_service.load_slots(location_id)
        slots = slot_data["slots"]

        cap = VideoReader(video_path).open()

        latest_results = []
        frame_index = 0

        while True:
            success, frame = cap.read()
            if not success:
                break

            if self.frame_sampler.should_process(frame_index):
                detections = self.detector.detect_vehicles(frame)
                latest_results = self.mapper.map_detections_to_slots(slots, detections)

            frame_index += 1

        cap.release()

        total_slots = len(latest_results)
        occupied_count = sum(1 for s in latest_results if s["occupied"])
        available_count = total_slots - occupied_count

        return {
            "location_id": location_id,
            "total_slots": total_slots,
            "occupied_count": occupied_count,
            "available_count": available_count,
            "slots": latest_results
        }
