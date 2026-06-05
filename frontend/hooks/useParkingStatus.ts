import { useCallback, useEffect, useRef, useState } from "react";
import {
  getParkingDemoStatus,
  getParkingVideoSnapshotStatus,
} from "../api/parkingApi";
import type {
  ParkingStatusResponse,
  ParkingVideoVariant,
} from "../types/parking";

type StatusMode = "demo" | "video_snapshot";
const DEFAULT_VIDEO_FRAME_INDEX = 0;
// Avoid firing YOLO analysis for tiny playback movements; video status is
// expensive and does not need to update on every rendered frame.
const MIN_SYNC_FRAME_DISTANCE = 15;

export function useParkingStatus(
  locationId: "fci" | "faie",
  variant?: ParkingVideoVariant
) {
  const [data, setData] = useState<ParkingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
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
      const result = await getParkingVideoSnapshotStatus(
        locationId,
        frameIndex,
        true,
        true,
        variant
      );
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
  }, [locationId, variant]);

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
        true,
        variant
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
  }, [locationId, variant]);

  const fetchDemoStatus = useCallback(async () => {
    try {
      setDemoLoading(true);
      setError(null);
      const result = await getParkingDemoStatus(locationId, variant);
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
  }, [locationId, variant]);

  useEffect(() => {
    lastSyncedFrame.current = null;
    hasLoaded.current = false;
    setLoading(true);
    fetchVideoSnapshot(DEFAULT_VIDEO_FRAME_INDEX);
  }, [fetchVideoSnapshot, variant]);

  return {
    data,
    loading,
    refreshing,
    snapshotLoading,
    demoLoading,
    error,
    lastUpdated,
    statusMode,
    refetch: () => fetchVideoSnapshot(DEFAULT_VIDEO_FRAME_INDEX),
    fetchDemoStatus,
    syncVideoFrame,
  };
}
