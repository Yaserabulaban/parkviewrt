import { getParkingVideoUrl } from '@/api/parkingApi';

interface ParkingVideoPreviewProps {
  locationId: 'fci' | 'faie';
  title: string;
}

export default function ParkingVideoPreview({
  locationId,
  title,
}: ParkingVideoPreviewProps) {
  return (
    <aside className="h-fit rounded-lg bg-white p-5 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
        <span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
          Video
        </span>
      </div>

      <video
        className="aspect-video w-full rounded-md bg-black object-cover"
        controls
        muted
        loop
        playsInline
        preload="metadata"
        src={getParkingVideoUrl(locationId)}
      />
    </aside>
  );
}
