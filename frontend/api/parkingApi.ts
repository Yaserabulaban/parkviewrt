import { API_BASE_URL } from "../config/env";
import type {
  ParkingStatusResponse,
  ParkingVideoMetadata,
  VideoSamplesResponse,
} from "../types/parking";

export async function getParkingStatus(
  locationId: "fci" | "faie"
): Promise<ParkingStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/status/${locationId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch parking status for ${locationId}`);
  }

  return response.json();
}

export async function getParkingDemoStatus(
  locationId: "fci" | "faie"
): Promise<ParkingStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/status/${locationId}/demo`);

  if (!response.ok) {
    throw new Error(`Failed to fetch demo parking status for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoSnapshotStatus(
  locationId: "fci" | "faie",
  frameIndex = 0,
  useCache = true,
  saveResult = true
): Promise<ParkingStatusResponse> {
  const params = new URLSearchParams({
    frame_index: String(frameIndex),
    use_cache: String(useCache),
    save_result: String(saveResult),
  });
  const response = await fetch(
    `${API_BASE_URL}/api/status/${locationId}/video-snapshot?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch video snapshot status for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoMetadata(
  locationId: "fci" | "faie"
): Promise<ParkingVideoMetadata> {
  const response = await fetch(`${API_BASE_URL}/api/video/${locationId}/metadata`);

  if (!response.ok) {
    throw new Error(`Failed to fetch video metadata for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoSamplesStatus(
  locationId: "fci" | "faie",
  sampleCount = 5,
  startFrame = 0,
  frameStep = 30
): Promise<VideoSamplesResponse> {
  const params = new URLSearchParams({
    sample_count: String(sampleCount),
    start_frame: String(startFrame),
    frame_step: String(frameStep),
  });
  const response = await fetch(
    `${API_BASE_URL}/api/status/${locationId}/video-samples?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch video sample status for ${locationId}`);
  }

  return response.json();
}

export function getParkingDebugImageUrl(
  locationId: "fci" | "faie",
  frameIndex = 0,
  source: "video" | "static" = "video"
) {
  const params = new URLSearchParams({
    source,
    frame_index: String(frameIndex),
  });
  return `${API_BASE_URL}/api/debug/${locationId}?${params.toString()}`;
}

export function getParkingVideoUrl(locationId: "fci" | "faie", version?: string) {
  const params = version ? `?v=${encodeURIComponent(version)}` : "";
  return `${API_BASE_URL}/api/video/${locationId}${params}`;
}
