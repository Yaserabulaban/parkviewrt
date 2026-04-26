interface ParkingSlotProps {
  id: string;
  isOccupied: boolean;
}

export default function ParkingSlot({ id, isOccupied }: ParkingSlotProps) {
  return (
    <div
      className={`
        w-24 h-32 border-4 rounded-lg flex items-center justify-center
        font-bold text-white transition-colors duration-300
        ${isOccupied 
          ? 'bg-red-500 border-red-700' 
          : 'bg-green-500 border-green-700'
        }
      `}
    >
      <span className="text-lg">{id}</span>
    </div>
  );
}
