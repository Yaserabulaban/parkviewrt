import argparse
from math import floor

from app.services.occupancy import ParkingOccupancyService
from app.services.video_snapshot import VideoSnapshotService


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pre-cache parking occupancy results for video playback."
    )
    parser.add_argument("location_id", choices=["fci", "faie"])
    parser.add_argument(
        "--variant",
        choices=["day", "night"],
        default=None,
        help="Video variant to cache. Defaults to the location default.",
    )
    parser.add_argument(
        "--seconds-step",
        type=float,
        default=2.0,
        help="Analyze one frame every N seconds.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Optional cap for quick smoke runs.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    service = VideoSnapshotService(ParkingOccupancyService())
    metadata = service.get_video_metadata(args.location_id, variant=args.variant)
    frame_step = max(1, floor(metadata["fps"] * args.seconds_step))
    frame_count = metadata["frame_count"]
    frame_indices = list(range(0, frame_count, frame_step))

    if args.max_frames is not None:
        frame_indices = frame_indices[: args.max_frames]

    for index, frame_index in enumerate(frame_indices, start=1):
        status = service.get_snapshot_status(
            args.location_id,
            variant=args.variant,
            frame_index=frame_index,
            use_cache=True,
            save_result=True,
        )
        source = status["source"]
        print(
            f"{index}/{len(frame_indices)} "
            f"frame={source['frame_index']} "
            f"occupied={status['occupied_count']} "
            f"available={status['available_count']} "
            f"cached={source.get('cached', False)}"
        )


if __name__ == "__main__":
    main()
