import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowLeft, ExternalLink, Film, RefreshCw } from 'lucide-react';
import { Switch } from './ui/switch';
import ParkingSlot from '../components/ParkingSlot';
import logoImage from '@/assets/mmu-logo.png';
import { useParkingStatus } from '@/hooks/useParkingStatus';
import { getParkingDebugImageUrl } from '@/api/parkingApi';

export default function FCIParkingView() {
  const navigate = useNavigate();
  const {
    data,
    loading,
    refreshing,
    snapshotLoading,
    sampleLoading,
    autoRefresh,
    setAutoRefresh,
    error,
    lastUpdated,
    refetch,
    fetchVideoSnapshot,
    fetchVideoSamples,
  } = useParkingStatus('fci');

  const monitoredSlotIds = new Set(['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8']);
  const rowGroups = [
    {
      label: 'Row A',
      upperStart: 1,
      lowerStart: 21,
    },
    {
      label: 'Row A',
      upperStart: 41,
      lowerStart: 61,
    },
  ];

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
  const debugImageUrl = getParkingDebugImageUrl('fci');
  const statusSourceLabel =
    data?.source?.type === 'video_snapshot'
      ? `Video frame ${data.source.frame_index}`
      : data?.source?.type === 'video_samples'
        ? `Video samples (${data.source.sample_count} frames)`
        : 'Static image';
  const busy = loading || refreshing || snapshotLoading || sampleLoading;

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
                disabled={busy}
                variant="outline"
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`}
                />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>

              <Button
                onClick={() => fetchVideoSnapshot(0)}
                disabled={busy}
                variant="outline"
              >
                <Film className="mr-2 h-4 w-4" />
                {snapshotLoading ? 'Sampling...' : 'Video Snapshot'}
              </Button>

              <Button
                onClick={() => fetchVideoSamples()}
                disabled={busy}
                variant="outline"
              >
                <Film className="mr-2 h-4 w-4" />
                {sampleLoading ? 'Sampling...' : 'Video Samples'}
              </Button>

              <Button asChild variant="outline">
                <a href={debugImageUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Detection Debug
                </a>
              </Button>

              <label className="flex items-center gap-2 text-sm text-gray-700">
                <Switch
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                  disabled={loading}
                />
                Auto refresh
              </label>

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
            Parking Layout - FCI Row Plan
          </h2>

          <div className="overflow-x-auto">
            <div className="mx-auto min-w-[1180px] rounded-lg border border-slate-200 bg-[#747a78] p-6 shadow-inner">
              <div className="mb-5 flex items-center justify-end">
                <div className="rounded bg-[#86a66f] px-4 py-2 text-xs font-semibold text-white">
                  Faculty / Tree Line
                </div>
              </div>

              <div className="space-y-8">
                {rowGroups.map((row) => (
                  <div key={row.label} className="rounded-md bg-[#656b69] p-4">
                    <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-100">
                      <span>{row.label}</span>
                    </div>

                    <div
                      className="grid gap-2"
                      style={{ gridTemplateColumns: 'repeat(20, minmax(0, 1fr))' }}
                    >
                      {Array.from({ length: 20 }, (_, index) => {
                        const id = `A${row.upperStart + index}`;
                        const monitored = monitoredSlotIds.has(id);
                        return (
                          <ParkingSlot
                            key={id}
                            id={id}
                            isOccupied={slotsMap.get(id) ?? false}
                            monitored={monitored}
                            size="map"
                            className="h-14 w-10"
                          />
                        );
                      })}
                    </div>

                    <div className="relative my-4 flex h-16 items-center justify-center rounded bg-[#4f5554]">
                      <div className="w-full border-t-2 border-dashed border-yellow-300/80" />
                      <span className="absolute rounded bg-[#4f5554] px-4 py-1 text-xs font-semibold text-slate-100">
                        Main Drive Lane
                      </span>
                    </div>

                    <div
                      className="grid gap-2"
                      style={{ gridTemplateColumns: 'repeat(20, minmax(0, 1fr))' }}
                    >
                      {Array.from({ length: 20 }, (_, index) => {
                        const id = `A${row.lowerStart + index}`;
                        const monitored = monitoredSlotIds.has(id);
                        return (
                          <ParkingSlot
                            key={id}
                            id={id}
                            isOccupied={slotsMap.get(id) ?? false}
                            monitored={monitored}
                            size="map"
                            className="h-14 w-10"
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex items-center justify-between">
                <div className="rounded bg-[#86a66f] px-4 py-2 text-xs font-semibold text-white">
                  Entrance / Exit Road
                </div>
                <div className="flex items-center gap-3 rounded bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700">
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
        </div>
      </div>
    </div>
  );
}
