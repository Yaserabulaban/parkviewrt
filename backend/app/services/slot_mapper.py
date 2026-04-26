from shapely.geometry import Polygon, box


class SlotMapper:
    def __init__(self, overlap_threshold: float = 0.20):
        self.overlap_threshold = overlap_threshold

    def map_detections_to_slots(self, slots: list, detections: list) -> list:
        results = []

        for slot in slots:
            slot_poly = Polygon(slot["points"])
            slot_area = slot_poly.area
            occupied = False

            for detection in detections:
                x1, y1, x2, y2 = detection["bbox"]
                det_box = box(x1, y1, x2, y2)

                inter_area = slot_poly.intersection(det_box).area
                overlap_ratio = inter_area / slot_area if slot_area > 0 else 0

                if overlap_ratio >= self.overlap_threshold:
                    occupied = True
                    break

            results.append({
                "slot_id": slot["slot_id"],
                "occupied": occupied
            })

        return results