interface ParkingSlotProps {
  id: string;
  isOccupied: boolean;
  className?: string;
  monitored?: boolean;
  size?: 'default' | 'map';
}

export default function ParkingSlot({
  id,
  isOccupied,
  className = '',
  monitored = true,
  size = 'default',
}: ParkingSlotProps) {
  const sizeClass =
    size === 'map'
      ? 'h-16 w-10 border-2 text-xs'
      : 'h-32 w-24 border-4 text-lg';
  const stateClass = monitored
    ? isOccupied
      ? 'bg-red-500 border-red-700 text-white shadow-sm'
      : 'bg-green-500 border-green-700 text-white shadow-sm'
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
      title={monitored ? `${id} status` : `${id} not monitored`}
    >
      <span>{id}</span>
    </div>
  );
}
