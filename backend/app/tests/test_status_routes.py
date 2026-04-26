from pathlib import Path
from tempfile import gettempdir

from fastapi.testclient import TestClient

from app.api.routes import status as status_routes
from app.main import app


class FakeOccupancyService:
    detector = object()

    def get_status(
        self,
        location_id,
        overlap_threshold=None,
        box_overlap_threshold=None,
        confidence_threshold=None,
        image_size=None,
    ):
        if location_id not in {"fci", "faie"}:
            raise ValueError(f"Unknown location: {location_id}")

        return {
            "location_id": location_id,
            "total_slots": 2,
            "occupied_count": 1,
            "available_count": 1,
            "slots": [
                {"slot_id": "A1", "occupied": True},
                {"slot_id": "A2", "occupied": False},
            ],
        }

    def create_debug_image(
        self,
        location_id,
        overlap_threshold=None,
        box_overlap_threshold=None,
        confidence_threshold=None,
        image_size=None,
    ):
        if location_id not in {"fci", "faie"}:
            raise ValueError(f"Unknown location: {location_id}")

        debug_image_path = Path(gettempdir()) / "parkviewrt_test_debug.jpg"
        debug_image_path.write_bytes(b"\xff\xd8\xff\xd9")
        return debug_image_path


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr(status_routes, "occupancy_service", FakeOccupancyService())
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": False,
        "locations": ["fci", "faie"],
    }


def test_status_endpoint_returns_parking_counts(monkeypatch):
    monkeypatch.setattr(status_routes, "occupancy_service", FakeOccupancyService())
    client = TestClient(app)

    response = client.get("/api/status/fci")

    assert response.status_code == 200
    assert response.json() == {
        "location_id": "fci",
        "total_slots": 2,
        "occupied_count": 1,
        "available_count": 1,
        "slots": [
            {"slot_id": "A1", "occupied": True},
            {"slot_id": "A2", "occupied": False},
        ],
        "updated_at": None,
    }


def test_status_endpoint_accepts_tuning_query_params(monkeypatch):
    monkeypatch.setattr(status_routes, "occupancy_service", FakeOccupancyService())
    client = TestClient(app)

    response = client.get(
        "/api/status/faie",
        params={
            "threshold": 0.3,
            "box_threshold": 0.2,
            "confidence": 0.2,
            "image_size": 1600,
        },
    )

    assert response.status_code == 200
    assert response.json()["location_id"] == "faie"


def test_status_endpoint_rejects_unknown_location(monkeypatch):
    monkeypatch.setattr(status_routes, "occupancy_service", FakeOccupancyService())
    client = TestClient(app)

    response = client.get("/api/status/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown location: unknown"}


def test_debug_endpoint_returns_jpeg(monkeypatch):
    monkeypatch.setattr(status_routes, "occupancy_service", FakeOccupancyService())
    client = TestClient(app)

    response = client.get("/api/debug/fci")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content.startswith(b"\xff\xd8")
