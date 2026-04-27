import { useCallback, useEffect, useRef, useState } from "react";
import {
  getParkingDemoStatus,
  getParkingStatus,
  getParkingVideoSamplesStatus,
  getParkingVideoSnapshotStatus,
} from "../api/parkingApi";
import type { ParkingStatusResponse, VideoSamplesResponse } from "../types/parking";

type StatusMode = "static" | "demo" | "video_snapshot" | "video_samples";

export function useParkingStatus(locationId: "fci" | "faie") {
  const [data, setData] = useState<ParkingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [statusMode, setStatusMode] = useState<StatusMode>("static");
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const hasLoaded = useRef(false);

  const fetchStatus = useCallback(async () => {
    try {
      if (hasLoaded.current) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      const result = await getParkingStatus(locationId);
      setData(result);
      setStatusMode("static");
      setLastUpdated(new Date());
      hasLoaded.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [locationId]);

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
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    if (!autoRefresh) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (statusMode === "video_samples") {
        fetchVideoSamples();
      } else if (statusMode === "video_snapshot") {
        fetchVideoSnapshot(0);
      } else if (statusMode === "demo") {
        fetchDemoStatus();
      } else {
        fetchStatus();
      }
    }, 15000);

    return () => window.clearInterval(intervalId);
  }, [autoRefresh, fetchDemoStatus, fetchStatus, fetchVideoSamples, fetchVideoSnapshot, statusMode]);

  return {
    data,
    loading,
    refreshing,
    snapshotLoading,
    sampleLoading,
    demoLoading,
    autoRefresh,
    setAutoRefresh,
    error,
    lastUpdated,
    statusMode,
    refetch: fetchStatus,
    fetchDemoStatus,
    fetchVideoSnapshot,
    fetchVideoSamples,
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
