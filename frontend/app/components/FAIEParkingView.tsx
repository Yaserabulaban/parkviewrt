import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowLeft, ExternalLink, Film, RefreshCw } from 'lucide-react';
import ParkingSlot from '../components/ParkingSlot';
import logoImage from '@/assets/mmu-logo.png';
import { useParkingStatus } from '@/hooks/useParkingStatus';
import { getParkingDebugImageUrl } from '@/api/parkingApi';

export default function FAIEParkingView() {
  const navigate = useNavigate();
  const {
    data,
    loading,
    refreshing,
    snapshotLoading,
    error,
    lastUpdated,
    refetch,
    fetchVideoSnapshot,
  } = useParkingStatus('faie');

  const row1Ids = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8'];
  const row2Ids = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8'];
  const row3Ids = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8'];

  const slotsMap = new Map(
    (data?.slots ?? []).map((slot) => [slot.slot_id, slot.occupied])
  );

  const row1 = row1Ids.map((id) => ({
    id,
    isOccupied: slotsMap.get(id) ?? false,
  }));

  const row2 = row2Ids.map((id) => ({
    id,
    isOccupied: slotsMap.get(id) ?? false,
  }));

  const row3 = row3Ids.map((id) => ({
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
  const debugImageUrl = getParkingDebugImageUrl('faie');
  const statusSourceLabel = data?.source
    ? `Video frame ${data.source.frame_index}`
    : 'Static image';

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
              FAIE Parking
            </h1>

            <div className="mb-4 flex flex-wrap items-center gap-3">
              <Button
                onClick={refetch}
                disabled={loading || refreshing || snapshotLoading}
                variant="outline"
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
                />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>

              <Button
                onClick={() => fetchVideoSnapshot(0)}
                disabled={loading || refreshing || snapshotLoading}
                variant="outline"
              >
                <Film className="mr-2 h-4 w-4" />
                {snapshotLoading ? 'Sampling...' : 'Video Snapshot'}
              </Button>

              <Button asChild variant="outline">
                <a href={debugImageUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Detection Debug
                </a>
              </Button>

              <span className="text-sm text-gray-600">
                Last updated: {lastUpdatedLabel} | Source: {statusSourceLabel}
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
            Parking Layout - Perpendicular Parking
          </h2>

          <div className="space-y-8">
            <div>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-sm font-semibold text-gray-600 w-16">Row B</span>
                <div className="flex gap-6">
                  {row1.map((spot) => (
                    <ParkingSlot key={spot.id} id={spot.id} isOccupied={spot.isOccupied} />
                  ))}
                </div>
              </div>
              <div className="h-16 bg-gray-300 rounded-lg relative ml-20">
                <div className="absolute inset-0 flex justify-around items-center">
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-sm font-semibold text-gray-600 w-16">Row D</span>
                <div className="flex gap-6">
                  {row2.map((spot) => (
                    <ParkingSlot key={spot.id} id={spot.id} isOccupied={spot.isOccupied} />
                  ))}
                </div>
              </div>
              <div className="h-16 bg-gray-300 rounded-lg relative ml-20">
                <div className="absolute inset-0 flex justify-around items-center">
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                  <div className="h-1 w-16 bg-yellow-400 rounded"></div>
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-sm font-semibold text-gray-600 w-16">Row E</span>
                <div className="flex gap-6">
                  {row3.map((spot) => (
                    <ParkingSlot key={spot.id} id={spot.id} isOccupied={spot.isOccupied} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
