import type { SlotStatus } from '@/types/parking';

interface ParkingSlotProps {
  id: string;
  isOccupied: boolean;
  status?: SlotStatus;
  className?: string;
  monitored?: boolean;
  size?: 'default' | 'map';
}

export default function ParkingSlot({
  id,
  isOccupied,
  status,
  className = '',
  monitored = true,
  size = 'default',
}: ParkingSlotProps) {
  const resolvedStatus = status ?? (isOccupied ? 'occupied' : 'available');
  const sizeClass =
    size === 'map'
      ? 'h-16 w-10 border-2 text-xs'
      : 'h-32 w-24 border-4 text-lg';
  const stateClass = monitored
    ? statusClass(resolvedStatus)
    : 'bg-slate-200 border-slate-300 text-slate-500';

  return (
    <div
      className={`
        flex items-center justify-center rounded-md border-solid
        font-bold transition-colors duration-300
        ${sizeClass}
        ${stateClass}
        ${className}
      `}
      title={monitored ? `${id} ${resolvedStatus}` : `${id} not monitored`}
    >
      <span>{id}</span>
    </div>
  );
}

function statusClass(status: SlotStatus) {
  if (status === 'occupied') {
    return 'bg-red-500 border-red-700 text-white shadow-sm';
  }

  if (status === 'occluded') {
    return 'bg-amber-500 border-amber-700 text-white shadow-sm';
  }

  return 'bg-green-500 border-green-700 text-white shadow-sm';
}
