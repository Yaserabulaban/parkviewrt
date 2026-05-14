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
  const monitoredSlotLimit = videoVariant === 'day' ? 22 : 18;
  const monitoredSlotIds = new Set(
    Array.from({ length: monitoredSlotLimit }, (_, index) => `B${index + 1}`)
  );
  const slotGroups = faieSlotGroups[videoVariant];
  const renderSlot = (id: string, className = '') => (
    <ParkingSlot
      key={id}
      id={id}
      isOccupied={slotsMap.get(id) ?? false}
      monitored={monitoredSlotIds.has(id)}
      size="map"
      className={`!h-11 !w-7 shrink-0 text-[10px] ${className}`}
    />
  );
  const renderSlotRow = (slotIds: string[], className = '') => (
    <div
      className={`flex min-w-0 flex-nowrap justify-center gap-1.5 ${className}`}
    >
      {slotIds.map((id) => renderSlot(id))}
    </div>
  );
  const renderMainCurbSlots = () => (
    <div className="flex min-w-0 flex-nowrap items-center justify-between gap-10">
      {slotGroups.main.map((slotSet) => renderSlotRow(slotSet, 'shrink-0'))}
    </div>
  );
  const renderAngledSlot = (id: string) => (
    <div key={id} className="-rotate-[18deg] self-center">
      {renderSlot(id)}
    </div>
  );

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
            <h2 className="mb-6 text-2xl font-semibold text-gray-800">
              Parking Layout - FAIE U Shape
            </h2>

            <div className="relative mx-auto aspect-[16/9] min-h-[520px] w-full max-w-[1120px] overflow-hidden rounded-lg border border-slate-200 bg-[#747a78] p-4 shadow-inner">
              <div className="absolute inset-x-0 top-0 h-[18%] bg-[#86a66f]" />
              <div className="absolute left-4 top-4 rounded bg-[#86a66f] px-3 py-2 text-xs font-semibold text-white">
                Tree Line / Faculty Side
              </div>
              {/* <div className="absolute right-4 bottom-4 rounded bg-[#656b69] px-3 py-2 text-xs font-semibold text-slate-100">
                Entrance / Exit Road
              </div> */}

              <div
                className="absolute rounded bg-[#4f5554]"
                style={{
                  left: faieLayoutTuning.roadLeft,
                  right: faieLayoutTuning.roadRight,
                  top: faieLayoutTuning.topRoadTop,
                  height: faieLayoutTuning.roadThickness,
                }}
              />
              <div
                className="absolute rounded bg-[#4f5554]"
                style={{
                  right: faieLayoutTuning.roadRight,
                  top: faieLayoutTuning.topRoadTop,
                  bottom: faieLayoutTuning.bottomRoadBottom,
                  width: faieLayoutTuning.roadThickness,
                }}
              />
              <div
                className="absolute rounded bg-[#4f5554]"
                style={{
                  left: faieLayoutTuning.roadLeft,
                  right: faieLayoutTuning.roadRight,
                  bottom: faieLayoutTuning.bottomRoadBottom,
                  height: faieLayoutTuning.roadThickness,
                }}
              />

              <div
                className="absolute border-t-2 border-dashed border-yellow-300/80"
                style={{
                  left: faieLayoutTuning.laneLineHorizontalInset,
                  right: faieLayoutTuning.laneLineHorizontalInset,
                  top: faieLayoutTuning.topLaneLineTop,
                }}
              />
              <div
                className="absolute border-l-2 border-dashed border-yellow-300/80"
                style={{
                  right: faieLayoutTuning.verticalLaneLineRight,
                  top: faieLayoutTuning.verticalLaneLineTop,
                  bottom: faieLayoutTuning.verticalLaneLineBottom,
                }}
              />
              <div
                className="absolute border-t-2 border-dashed border-yellow-300/80"
                style={{
                  left: faieLayoutTuning.laneLineHorizontalInset,
                  right: faieLayoutTuning.laneLineHorizontalInset,
                  bottom: faieLayoutTuning.bottomLaneLineBottom,
                }}
              />

              <div
                className="absolute"
                style={{
                  left: faieLayoutTuning.topSlotsLeft,
                  right: faieLayoutTuning.topSlotsRight,
                  top: faieLayoutTuning.topSlotsTop,
                }}
              >
                {renderMainCurbSlots()}
              </div>

              <div
                className="absolute flex flex-col justify-between"
                style={{
                  right: faieLayoutTuning.angledSlotsRight,
                  top: faieLayoutTuning.angledSlotsTop,
                  bottom: faieLayoutTuning.angledSlotsBottom,
                  width: faieLayoutTuning.angledSlotsWidth,
                }}
              >
                {slotGroups.angled.map(renderAngledSlot)}
              </div>

              <div
                className="absolute p-3"
                style={{
                  left: faieLayoutTuning.middleSlotsLeft,
                  right: faieLayoutTuning.middleSlotsRight,
                  top: faieLayoutTuning.middleSlotsTop,
                }}
              >
                {renderSlotRow(slotGroups.middle)}
              </div>

              <div className="absolute bottom-4 left-4 flex items-center gap-3 rounded bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700">
                  <span className="inline-block h-3 w-3 rounded bg-red-500" />
                  Occupied
                  <span className="inline-block h-3 w-3 rounded bg-green-500" />
                  Available
                  <span className="inline-block h-3 w-3 rounded bg-slate-300" />
                  Not monitored
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

function rangeSlots(start: number, end: number) {
  return Array.from({ length: end - start + 1 }, (_, index) => `B${start + index}`);
}

const faieSlotGroups = {
  day: {
    main: [rangeSlots(1, 15), rangeSlots(23, 25)],
    angled: rangeSlots(26, 31),
    middle: [...rangeSlots(16, 22), ...rangeSlots(32, 40)],
  },
  night: {
    main: [rangeSlots(1, 15), rangeSlots(19, 25)],
    angled: rangeSlots(26, 31),
    middle: [...rangeSlots(16, 18), ...rangeSlots(32, 40)],
  },
};

const faieLayoutTuning = {
  roadLeft: '9%',
  roadRight: '12%',
  roadThickness: '10%',
  topRoadTop: '33%',
  bottomRoadBottom: '15%',
  laneLineHorizontalInset: '17%',
  topLaneLineTop: '37.5%',
  bottomLaneLineBottom: '20.5%',
  verticalLaneLineRight: '17%',
  verticalLaneLineTop: '38%',
  verticalLaneLineBottom: '21%',
  topSlotsLeft: '10%',
  topSlotsRight: '10%',
  topSlotsTop: '23%',
  angledSlotsRight: '3%',
  angledSlotsTop: '33%',
  angledSlotsBottom: '18%',
  angledSlotsWidth: '11%',
  middleSlotsLeft: '20%',
  middleSlotsRight: '30%',
  middleSlotsTop: '51%',
};
