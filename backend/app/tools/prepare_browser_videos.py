import shutil
import subprocess
from pathlib import Path

import cv2


BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "data" / "videos"
SOURCE_EXTENSIONS = (".mov", ".avi", ".mkv", ".mp4")
LOCATIONS = ("fci", "faie")
VARIANTS = ("day", "night")
BROWSER_VIDEO_SUFFIX = "_browser.mp4"


def find_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "FFmpeg is required. Install FFmpeg or run "
            "'py -3.11 -m pip install imageio-ffmpeg'."
        ) from exc

    return imageio_ffmpeg.get_ffmpeg_exe()


def find_source_video(location_id: str, variant: str) -> Path:
    video_dir = VIDEOS_DIR / location_id / variant
    if not video_dir.exists():
        raise FileNotFoundError(f"Video directory does not exist: {video_dir}")

    files = [
        path
        for path in video_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in SOURCE_EXTENSIONS
        and not path.name.lower().endswith(BROWSER_VIDEO_SUFFIX)
    ]
    for extension in SOURCE_EXTENSIONS:
        matches = sorted(
            path for path in files if path.suffix.lower() == extension
        )
        if matches:
            return matches[0]

    raise FileNotFoundError(f"No source video found in: {video_dir}")


def read_codec(video_path: Path) -> str:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Unable to inspect video: {video_path}")

    try:
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    finally:
        cap.release()

    return "".join(chr((fourcc >> (8 * index)) & 0xFF) for index in range(4)).lower()


def find_current_browser_copy(source_path: Path) -> Path | None:
    candidates = [
        source_path.with_name(f"{source_path.stem}{BROWSER_VIDEO_SUFFIX}"),
    ]
    for candidate in candidates:
        if (
            candidate != source_path
            and candidate.exists()
            and candidate.stat().st_mtime >= source_path.stat().st_mtime
            and read_codec(candidate) in {"h264", "avc1"}
        ):
            return candidate
    return None


def prepare_browser_video(ffmpeg_path: str, source_path: Path) -> Path:
    current_copy = find_current_browser_copy(source_path)
    if current_copy is not None:
        print(f"Using current H.264 browser copy: {current_copy.name}")
        return current_copy

    output_path = source_path.with_name(f"{source_path.stem}{BROWSER_VIDEO_SUFFIX}")
    temporary_path = source_path.with_name(f"{source_path.stem}_browser.pending.mp4")
    codec = read_codec(source_path)

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(source_path),
        "-map",
        "0:v:0",
        "-an",
    ]
    if codec in {"h264", "avc1"}:
        command.extend(["-c:v", "copy"])
    else:
        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
            ]
        )
    command.extend(["-movflags", "+faststart", str(temporary_path)])

    print(f"Preparing {output_path.name} from {source_path.name} ({codec})")
    subprocess.run(command, check=True)
    temporary_path.replace(output_path)
    return output_path


def main() -> None:
    ffmpeg_path = find_ffmpeg()
    for location_id in LOCATIONS:
        for variant in VARIANTS:
            source_path = find_source_video(location_id, variant)
            output_path = prepare_browser_video(ffmpeg_path, source_path)
            print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
