import { useCallback, useEffect, useRef, useState } from "react";
import { getParkingStatus } from "../api/parkingApi";
import type { ParkingStatusResponse } from "../types/parking";

export function useParkingStatus(locationId: "fci" | "faie") {
  const [data, setData] = useState<ParkingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
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
      setLastUpdated(new Date());
      hasLoaded.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [locationId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    data,
    loading,
    refreshing,
    error,
    lastUpdated,
    refetch: fetchStatus,
  };
}