import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowLeft, ExternalLink, RefreshCw } from 'lucide-react';
import ParkingSlot from '../components/ParkingSlot';
import logoImage from '@/assets/mmu-logo.png';
import { useParkingStatus } from '@/hooks/useParkingStatus';
import { getParkingDebugImageUrl } from '@/api/parkingApi';

export default function FCIParkingView() {
  const navigate = useNavigate();
  const { data, loading, refreshing, error, lastUpdated, refetch } = useParkingStatus('fci');

  const leftSlotIds = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8'];
  const rightSlotIds = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8'];

  const slotsMap = new Map(
    (data?.slots ?? []).map((slot) => [slot.slot_id, slot.occupied])
  );

  const leftSide = leftSlotIds.map((id) => ({
    id,
    isOccupied: slotsMap.get(id) ?? false,
  }));

  const rightSide = rightSlotIds.map((id) => ({
    id,
    isOccupied: slotsMap.get(id) ?? false,
  }));

  const occupiedCount = data?.occupied_count ?? 0;
  const availableCount = data?.available_count ?? 0;
  const lastUpdatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : 'Not updated yet';
  const debugImageUrl = getParkingDebugImageUrl('fci');

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <Button
              onClick={() => navigate('/')}
              variant="outline"
              className="mb-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Button>

            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              FCI Parking
            </h1>

            <div className="mb-4 flex flex-wrap items-center gap-3">
              <Button
                onClick={refetch}
                disabled={loading || refreshing}
                variant="outline"
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
                />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>

              <Button asChild variant="outline">
                <a href={debugImageUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Detection Debug
                </a>
              </Button>

              <span className="text-sm text-gray-600">
                Last updated: {lastUpdatedLabel}
              </span>
            </div>

            {loading && (
              <p className="text-blue-600 mb-4">Loading parking status...</p>
            )}

            {error && (
              <p className="text-red-600 mb-4">Error: {error}</p>
            )}

            <div className="flex gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
                <div className="w-6 h-6 bg-green-500 rounded"></div>
                <span className="text-lg">Available: {availableCount}</span>
              </div>
              <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
                <div className="w-6 h-6 bg-red-500 rounded"></div>
                <span className="text-lg">Occupied: {occupiedCount}</span>
              </div>
            </div>
          </div>

          <img
            src={logoImage}
            alt="MMU Logo"
            className="w-48"
          />
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">
            Parking Layout - Angled Parking
          </h2>

          <div className="relative">
            <div className="flex gap-12 justify-center">
              <div className="flex flex-col gap-4">
                <div className="text-center text-sm font-semibold text-gray-600 mb-2">
                  Row A
                </div>
                {leftSide.map((spot) => (
                  <div key={spot.id} className="transform -rotate-45 origin-right">
                    <ParkingSlot id={spot.id} isOccupied={spot.isOccupied} />
                  </div>
                ))}
              </div>

              <div className="w-32 bg-gray-300 rounded-lg flex items-center justify-center relative">
                <div className="absolute inset-0 flex flex-col justify-around py-4">
                  <div className="w-1 h-12 bg-yellow-400 mx-auto rounded"></div>
                  <div className="w-1 h-12 bg-yellow-400 mx-auto rounded"></div>
                  <div className="w-1 h-12 bg-yellow-400 mx-auto rounded"></div>
                  <div className="w-1 h-12 bg-yellow-400 mx-auto rounded"></div>
                </div>
                <div className="transform -rotate-90 text-gray-600 font-semibold text-sm whitespace-nowrap">
                  Main Drive
                </div>
              </div>

              <div className="flex flex-col gap-4">
                <div className="text-center text-sm font-semibold text-gray-600 mb-2">
                  Row F
                </div>
                {rightSide.map((spot) => (
                  <div key={spot.id} className="transform rotate-45 origin-left">
                    <ParkingSlot id={spot.id} isOccupied={spot.isOccupied} />
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 flex justify-between text-sm font-semibold text-gray-600">
              <div>Entrance</div>
              <div>Exit</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
