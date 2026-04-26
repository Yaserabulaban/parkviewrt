import { useEffect, useState } from "react";
import { getParkingStatus } from "../api/parkingApi";
import type { ParkingStatusResponse } from "../types/parking";

export function useParkingStatus(locationId: "fci" | "faie") {
  const [data, setData] = useState<ParkingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getParkingStatus(locationId);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [locationId]);

  return {
    data,
    loading,
    error,
    refetch: fetchStatus,
  };
}