import { useCallback, useEffect, useRef, useState } from "react";
import {
  getParkingDemoStatus,
  getParkingVideoSamplesStatus,
  getParkingVideoSnapshotStatus,
} from "../api/parkingApi";
import type { ParkingStatusResponse, VideoSamplesResponse } from "../types/parking";

type StatusMode = "demo" | "video_snapshot" | "video_samples";
const DEFAULT_VIDEO_FRAME_INDEX = 0;
const MIN_SYNC_FRAME_DISTANCE = 15;

export function useParkingStatus(locationId: "fci" | "faie") {
  const [data, setData] = useState<ParkingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [statusMode, setStatusMode] = useState<StatusMode>("video_snapshot");
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const hasLoaded = useRef(false);
  const syncRequestInFlight = useRef(false);
  const lastSyncedFrame = useRef<number | null>(null);

  const fetchVideoSnapshot = useCallback(async (frameIndex = 0) => {
    try {
      setSnapshotLoading(true);
      setError(null);
      const result = await getParkingVideoSnapshotStatus(locationId, frameIndex);
      setData(result);
      setStatusMode("video_snapshot");
      setLastUpdated(new Date());
      hasLoaded.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setSnapshotLoading(false);
      setRefreshing(false);
    }
  }, [locationId]);

  const syncVideoFrame = useCallback(async (frameIndex: number) => {
    const normalizedFrameIndex = Math.max(0, Math.floor(frameIndex));
    if (
      syncRequestInFlight.current ||
      (
        lastSyncedFrame.current !== null &&
        Math.abs(normalizedFrameIndex - lastSyncedFrame.current) < MIN_SYNC_FRAME_DISTANCE
      )
    ) {
      return;
    }

    syncRequestInFlight.current = true;
    lastSyncedFrame.current = normalizedFrameIndex;

    try {
      setRefreshing(true);
      setError(null);
      const result = await getParkingVideoSnapshotStatus(
        locationId,
        normalizedFrameIndex,
        true,
        true
      );
      setData(result);
      setStatusMode("video_snapshot");
      setLastUpdated(new Date());
      hasLoaded.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setRefreshing(false);
      syncRequestInFlight.current = false;
    }
  }, [locationId]);

  const fetchDemoStatus = useCallback(async () => {
    try {
      setDemoLoading(true);
      setError(null);
      const result = await getParkingDemoStatus(locationId);
      setData(result);
      setStatusMode("demo");
      setLastUpdated(new Date());
      hasLoaded.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setDemoLoading(false);
    }
  }, [locationId]);

  const fetchVideoSamples = useCallback(
    async (sampleCount = 5, startFrame = 0, frameStep = 30) => {
      try {
        setSampleLoading(true);
        setError(null);
        const result = await getParkingVideoSamplesStatus(
          locationId,
          sampleCount,
          startFrame,
          frameStep
        );
        setData(mapVideoSamplesToStatus(result));
        setStatusMode("video_samples");
        setLastUpdated(new Date());
        hasLoaded.current = true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
        setSampleLoading(false);
      }
    },
    [locationId]
  );

  useEffect(() => {
    fetchVideoSnapshot(DEFAULT_VIDEO_FRAME_INDEX);
  }, [fetchVideoSnapshot]);

  return {
    data,
    loading,
    refreshing,
    snapshotLoading,
    sampleLoading,
    demoLoading,
    error,
    lastUpdated,
    statusMode,
    refetch: () => fetchVideoSnapshot(DEFAULT_VIDEO_FRAME_INDEX),
    fetchDemoStatus,
    fetchVideoSnapshot,
    fetchVideoSamples,
    syncVideoFrame,
  };
}

function mapVideoSamplesToStatus(
  result: VideoSamplesResponse
): ParkingStatusResponse {
  return {
    location_id: result.location_id,
    total_slots: result.summary.total_slots,
    occupied_count: result.summary.occupied_count,
    available_count: result.summary.available_count,
    slots: result.summary.slots.map((slot) => ({
      slot_id: slot.slot_id,
      occupied: slot.occupied,
    })),
    source: result.source,
  };
}
