import { useEffect, useRef, useState } from 'react';
import { getParkingVideoMetadata, getParkingVideoUrl } from '@/api/parkingApi';
import type { ParkingVideoMetadata } from '@/types/parking';

interface ParkingVideoPreviewProps {
  locationId: 'fci' | 'faie';
  title: string;
  onFrameChange?: (frameIndex: number) => void;
}

export default function ParkingVideoPreview({
  locationId,
  title,
  onFrameChange,
}: ParkingVideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [metadata, setMetadata] = useState<ParkingVideoMetadata | null>(null);
  const [metadataError, setMetadataError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    getParkingVideoMetadata(locationId)
      .then((result) => {
        if (active) {
          setMetadata(result);
          setMetadataError(null);
        }
      })
      .catch((error) => {
        if (active) {
          setMetadataError(error instanceof Error ? error.message : 'Unable to load video metadata');
        }
      });

    return () => {
      active = false;
    };
  }, [locationId]);

  useEffect(() => {
    if (!metadata || !onFrameChange) {
      return;
    }

    const intervalId = window.setInterval(() => {
      const video = videoRef.current;
      if (!video || video.paused || video.ended) {
        return;
      }

      onFrameChange(Math.floor(video.currentTime * metadata.fps));
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [metadata, onFrameChange]);

  return (
    <aside className="h-fit rounded-lg bg-white p-5 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
        <span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
          Video
        </span>
      </div>

      <video
        ref={videoRef}
        className="aspect-video w-full rounded-md bg-black object-cover"
        controls
        muted
        loop
        playsInline
        preload="metadata"
        src={getParkingVideoUrl(locationId)}
      />

      <div className="mt-3 text-xs text-slate-600">
        {metadata ? (
          <span>
            {metadata.file_name} | {metadata.fps.toFixed(2)} fps | {metadata.frame_count} frames
          </span>
        ) : metadataError ? (
          <span className="text-red-600">{metadataError}</span>
        ) : (
          <span>Loading video metadata...</span>
        )}
      </div>
    </aside>
  );
}
