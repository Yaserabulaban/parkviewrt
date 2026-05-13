import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowLeft, ExternalLink, RefreshCw, Shuffle } from 'lucide-react';
import { useState } from 'react';
import ParkingSlot from '../components/ParkingSlot';
import ParkingVideoPreview from '../components/ParkingVideoPreview';
import logoImage from '@/assets/mmu-logo.png';
import { useParkingStatus } from '@/hooks/useParkingStatus';
import { getParkingDebugImageUrl } from '@/api/parkingApi';

export default function FAIEParkingView() {
  const navigate = useNavigate();
  const [videoVariant, setVideoVariant] = useState<'day' | 'night'>('day');
  const {
    data,
    loading,
    refreshing,
    demoLoading,
    error,
    lastUpdated,
    statusMode,
    refetch,
    fetchDemoStatus,
    syncVideoFrame,
  } = useParkingStatus('faie', videoVariant);

  const uShapeSlots = [
    'B1',
    'B2',
    'B3',
    'B4',
    'B5',
    'B6',
    'B7',
    'B8',
    'B9',
    'B10',
    'B11',
    'B12',
    'B13',
    'B14',
    'B15',
    'B16',
    'B17',
    'B18',
    'B19',
    'B20',
    'B21',
    'B22',
    'B23',
    'B24',
    'B25',
    'B26',
    'B27',
    'B28',
    'B29',
    'B30',
  ];
  const baseSlots = uShapeSlots.slice(0, 25);
  const rightSideSlots = uShapeSlots.slice(25);
  const centerSlots = Array.from({ length: 10 }, (_, index) => `B${index + 31}`);

  const slotsMap = new Map(
    (data?.slots ?? []).map((slot) => [slot.slot_id, slot.occupied])
  );

  const occupiedCount = data?.occupied_count ?? 0;
  const availableCount = data?.available_count ?? 0;
  const lastUpdatedLabel = lastUpdated
    ? lastUpdated.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : 'Not updated yet';
  const debugFrameIndex = data?.source?.type === 'video_snapshot'
    ? data.source.frame_index
    : 0;
  const debugImageUrl = getParkingDebugImageUrl(
    'faie',
    debugFrameIndex,
    'video',
    videoVariant
  );
  const statusSourceLabel =
    data?.source?.type === 'video_snapshot'
      ? `Video frame ${data.source.frame_index}`
      : statusMode === 'demo'
          ? 'Demo random'
          : 'Static image';
  const busy = loading || refreshing || demoLoading;

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
              <div className="flex rounded-md border border-slate-300 bg-white p-1">
                {(['day', 'night'] as const).map((variant) => (
                  <button
                    key={variant}
                    type="button"
                    onClick={() => setVideoVariant(variant)}
                    className={`rounded px-3 py-2 text-sm font-semibold transition ${
                      videoVariant === variant
                        ? 'bg-slate-900 text-white'
                        : 'text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {variant === 'day' ? 'Day' : 'Night'}
                  </button>
                ))}
              </div>

              <Button
                onClick={refetch}
                disabled={busy}
                variant="outline"
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
                />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>

              <Button
                onClick={fetchDemoStatus}
                disabled={busy}
                variant="outline"
              >
                <Shuffle className="mr-2 h-4 w-4" />
                {demoLoading ? 'Shuffling...' : 'Demo Random'}
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

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0 rounded-lg bg-white p-8 shadow-lg">
            <div className="overflow-x-auto">
              <div className="relative mx-auto h-[580px] max-w-[1200px] overflow-hidden rounded-lg border border-slate-200 bg-[#747a78] p-6 shadow-inner">
                <div className="absolute inset-x-0 top-0 h-24 bg-[#86a66f]" />

                <div className="absolute left-[70px] top-[220px] h-[88px] w-[896px] rounded-l-md bg-[#565d5b]" />
                <div className="absolute left-[58px] top-[410px] h-[88px] w-[896px] rounded-l-md bg-[#565d5b]" />
                <div className="absolute left-[900px] top-[220px] h-[278px] w-24 rounded-r-md bg-[#565d5b]" />
                <div className="absolute left-[100px] top-[262px] w-[780px] border-t-2 border-dashed border-yellow-300/80" />
                <div className="absolute left-[100px] top-[452px] w-[780px] border-t-2 border-dashed border-yellow-300/80" />
                <div className="absolute left-[948px] top-[252px] h-[200px] border-l-2 border-dashed border-yellow-300/80" />

                <div
                  className="absolute left-[42px] top-[126px] grid gap-1"
                  style={{ gridTemplateColumns: 'repeat(25, minmax(0, 1fr))' }}
                >
                  {baseSlots.map((id) => {
                    return (
                      <ParkingSlot
                        key={id}
                        id={id}
                        isOccupied={slotsMap.get(id) ?? false}
                        monitored={slotsMap.has(id)}
                        size="map"
                        className="h-14 w-8 text-[10px]"
                      />
                    );
                  })}
                </div>

                <div className="absolute left-[1100px] top-[200px] flex flex-col gap-3">
                  {rightSideSlots.map((id) => {
                    return (
                      <ParkingSlot
                        key={id}
                        id={id}
                        isOccupied={slotsMap.get(id) ?? false}
                        monitored={slotsMap.has(id)}
                        size="map"
                        className="h-14 w-8 -rotate-[20deg] text-[10px]"
                      />
                    );
                  })}
                </div>

                <div className="absolute left-[250px] top-[330px] grid grid-cols-10 gap-3">
                  {centerSlots.map((id) => (
                    <ParkingSlot
                      key={id}
                      id={id}
                      isOccupied={slotsMap.get(id) ?? false}
                      monitored={slotsMap.has(id)}
                      size="map"
                      className="h-14 w-8 text-[10px]"
                    />
                  ))}
                </div>

                <div className="absolute right-6 top-6 flex items-center gap-3 rounded bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700">
                  <span className="inline-block h-3 w-3 rounded bg-red-500" />
                  Occupied
                  <span className="inline-block h-3 w-3 rounded bg-green-500" />
                  Available
                  <span className="inline-block h-3 w-3 rounded bg-slate-300" />
                  Not monitored
                </div>
              </div>
            </div>
          </div>

          <ParkingVideoPreview
            locationId="faie"
            variant={videoVariant}
            title={`FAIE ${videoVariant === 'day' ? 'Day' : 'Night'} Footage`}
            onFrameChange={syncVideoFrame}
          />
        </div>
      </div>
    </div>
  );
}
