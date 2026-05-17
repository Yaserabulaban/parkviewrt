import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { ArrowLeft, ExternalLink, RefreshCw, Shuffle } from 'lucide-react';
import { useState } from 'react';
import ParkingSlot from '../components/ParkingSlot';
import ParkingVideoPreview from '../components/ParkingVideoPreview';
import logoImage from '@/assets/mmu-logo.png';
import { useParkingStatus } from '@/hooks/useParkingStatus';
import { getParkingDebugImageUrl } from '@/api/parkingApi';
import type { SlotStatus } from '@/types/parking';

export default function FCIParkingView() {
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
  } = useParkingStatus('fci', videoVariant);

  const variantLayout = fciVariantLayouts[videoVariant];
  const monitoredSlotIds = new Set(
    Array.from({ length: variantLayout.monitoredSlots }, (_, index) => `A${index + 1}`)
  );
  const slotGroups = variantLayout.slotGroups;

  const slotsMap = new Map(
    (data?.slots ?? []).map((slot) => [slot.slot_id, slot.occupied])
  );
  const slotStatusMap = new Map<string, SlotStatus>(
    (data?.slots ?? []).map((slot) => [
      slot.slot_id,
      slot.status ?? (slot.occupied ? 'occupied' : 'available'),
    ])
  );

  const occupiedCount = data?.occupied_count ?? 0;
  const availableCount = data?.available_count ?? 0;
  const occludedCount = data?.occluded_count ?? 0;
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
    'fci',
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
  const renderSlot = (id: string) => {
    const monitored = slotsMap.has(id) || monitoredSlotIds.has(id);

    return (
      <ParkingSlot
        key={id}
        id={id}
        isOccupied={slotsMap.get(id) ?? false}
        status={slotStatusMap.get(id)}
        monitored={monitored}
        size="map"
        className="!h-11 !w-8 shrink-0 text-[10px]"
      />
    );
  };
  const renderSlotRow = (slotIds: string[], className = '') => (
    <div className={`flex min-w-0 flex-nowrap gap-1 ${className}`}>
      {slotIds.map(renderSlot)}
    </div>
  );
  const roadBand = (label: string) => (
    <div className="relative flex h-12 items-center justify-center rounded bg-[#4f5554]">
      <div className="w-full border-t-2 border-dashed border-yellow-300/80" />
      <span className="absolute rounded bg-[#4f5554] px-4 py-1 text-xs font-semibold text-slate-100">
        {label}
      </span>
    </div>
  );
  const pavementBand = (
    <div className="flex h-6 items-center justify-center rounded bg-[#8b938f] text-[10px] font-semibold uppercase tracking-wide text-slate-100">
      Pavements
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-[1500px]">
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
              <div className="bg-white rounded-lg shadow p-4 flex items-center gap-3">
                <div className="w-6 h-6 bg-amber-500 rounded"></div>
                <span className="text-lg">Occluded: {occludedCount}</span>
              </div>
            </div>
          </div>

          <img
            src={logoImage}
            alt="MMU Logo"
            className="w-48"
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <div className="min-w-0 rounded-lg bg-white p-6 shadow-lg">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Parking Layout - FCI Row Plan
            </h2>

            <div className="overflow-hidden">
              <div className="mx-auto w-full max-w-[900px] rounded-lg border border-slate-200 bg-[#747a78] p-4 shadow-inner">
                <div className="mb-4 flex items-center justify-between">
                  <div className="w-56 rounded-md bg-[#656b69] p-2.5">
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-100">
                      Row A - Top Left Line
                    </div>
                    {renderSlotRow(slotGroups.isolated)}
                  </div>

                  <div className="rounded bg-[#86a66f] px-4 py-2 text-xs font-semibold text-white">
                    Faculty / Tree Line
                  </div>
                </div>

                <div className="space-y-4">
                  {roadBand('Top Drive Lane')}

                  <div className="overflow-hidden rounded-md bg-[#656b69] p-3">
                    <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-100">
                      Row A - Main Left Line
                    </div>
                    {renderSlotRow(slotGroups.upper)}
                    <div className="my-3">{pavementBand}</div>
                    <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-100">
                      Row A - Main Right Line
                    </div>
                    {renderSlotRow(slotGroups.middle)}
                  </div>

                  {roadBand('Middle Drive Lane')}

                  <div className="overflow-hidden rounded-md bg-[#656b69] p-3">
                    <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-100">
                      Row A - Lower Left Line
                    </div>
                    {renderSlotRow(slotGroups.lowerUpper)}
                    <div className="my-3">{pavementBand}</div>
                    <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-100">
                      Row A - Lower Right Line
                    </div>
                    {renderSlotRow(slotGroups.lowerBottom)}
                  </div>

                  {roadBand('Bottom Drive Lane')}
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
                    <span className="inline-block h-3 w-3 rounded bg-amber-500" />
                    Occluded
                    <span className="inline-block h-3 w-3 rounded bg-slate-300" />
                    Not monitored
                  </div>
                </div>
              </div>
            </div>
          </div>

          <ParkingVideoPreview
            locationId="fci"
            variant={videoVariant}
            title={`FCI ${videoVariant === 'day' ? 'Day' : 'Night'} Footage`}
            onFrameChange={syncVideoFrame}
          />
        </div>
      </div>
    </div>
  );
}

function rangeSlots(start: number, end: number) {
  return Array.from({ length: end - start + 1 }, (_, index) => `A${start + index}`);
}

const fciVisualSlotGroups = {
  isolated: rangeSlots(1, 6),
  upper: rangeSlots(7, 25),
  middle: rangeSlots(26, 47),
  lowerUpper: rangeSlots(48, 65),
  lowerBottom: rangeSlots(66, 78),
};

const fciVariantLayouts = {
  day: {
    monitoredSlots: 78,
    slotGroups: fciVisualSlotGroups,
  },
  night: {
    monitoredSlots: 77,
    slotGroups: fciVisualSlotGroups,
  },
};
