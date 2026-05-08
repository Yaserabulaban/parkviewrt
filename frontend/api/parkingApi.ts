import { API_BASE_URL } from "../config/env";
import type {
  ParkingStatusResponse,
  ParkingVideoVariant,
  ParkingVideoMetadata,
  VideoSamplesResponse,
} from "../types/parking";

export async function getParkingDemoStatus(
  locationId: "fci" | "faie",
  variant?: ParkingVideoVariant
): Promise<ParkingStatusResponse> {
  const params = new URLSearchParams();
  if (variant) {
    params.set("variant", variant);
  }
  const queryString = params.toString();
  const response = await fetch(
    `${API_BASE_URL}/api/status/${locationId}/demo${queryString ? `?${queryString}` : ""}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch demo parking status for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoSnapshotStatus(
  locationId: "fci" | "faie",
  frameIndex = 0,
  useCache = true,
  saveResult = true,
  variant?: ParkingVideoVariant
): Promise<ParkingStatusResponse> {
  const params = new URLSearchParams({
    frame_index: String(frameIndex),
    use_cache: String(useCache),
    save_result: String(saveResult),
  });
  if (variant) {
    params.set("variant", variant);
  }
  const response = await fetch(
    `${API_BASE_URL}/api/status/${locationId}/video-snapshot?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch video snapshot status for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoMetadata(
  locationId: "fci" | "faie",
  variant?: ParkingVideoVariant
): Promise<ParkingVideoMetadata> {
  const params = new URLSearchParams();
  if (variant) {
    params.set("variant", variant);
  }
  const queryString = params.toString();
  const response = await fetch(
    `${API_BASE_URL}/api/video/${locationId}/metadata${queryString ? `?${queryString}` : ""}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch video metadata for ${locationId}`);
  }

  return response.json();
}

export async function getParkingVideoSamplesStatus(
  locationId: "fci" | "faie",
  sampleCount = 5,
  startFrame = 0,
  frameStep = 30,
  variant?: ParkingVideoVariant
): Promise<VideoSamplesResponse> {
  const params = new URLSearchParams({
    sample_count: String(sampleCount),
    start_frame: String(startFrame),
    frame_step: String(frameStep),
  });
  if (variant) {
    params.set("variant", variant);
  }
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
  source: "video" | "static" = "video",
  variant?: ParkingVideoVariant
) {
  const params = new URLSearchParams({
    source,
    frame_index: String(frameIndex),
  });
  if (variant) {
    params.set("variant", variant);
  }
  return `${API_BASE_URL}/api/debug/${locationId}?${params.toString()}`;
}

export function getParkingVideoUrl(
  locationId: "fci" | "faie",
  version?: string,
  variant?: ParkingVideoVariant
) {
  const params = new URLSearchParams();
  if (version) {
    params.set("v", version);
  }
  if (variant) {
    params.set("variant", variant);
  }
  const queryString = params.toString();
  return `${API_BASE_URL}/api/video/${locationId}${queryString ? `?${queryString}` : ""}`;
}
