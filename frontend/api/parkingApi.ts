import { API_BASE_URL } from "../config/env";
import type { ParkingStatusResponse } from "../types/parking";

export async function getParkingStatus(
  locationId: "fci" | "faie"
): Promise<ParkingStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/status/${locationId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch parking status for ${locationId}`);
  }

  return response.json();
}

export function getParkingDebugImageUrl(locationId: "fci" | "faie") {
  return `${API_BASE_URL}/api/debug/${locationId}`;
}
