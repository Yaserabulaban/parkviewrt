export type SlotStatus = "occupied" | "empty";

export interface ParkingSlotDto {
  slot_id: string;
  occupied: boolean;
}

export interface VideoSnapshotSource {
  type: "video_snapshot";
  video_path: string;
  frame_index: number;
  cached?: boolean;
  cache_path?: string;
}

export interface ParkingVideoMetadata {
  location_id: "fci" | "faie";
  video_path: string;
  file_name: string;
  file_size: number;
  last_modified: number;
  frame_count: number;
  fps: number;
  duration_seconds: number;
}

export interface VideoSamplesSource {
  type: "video_samples";
  video_path: string;
  frame_count: number;
  fps: number;
  sample_count: number;
  start_frame: number;
  frame_step: number;
  frame_indices: number[];
}

export interface ParkingStatusResponse {
  location_id: "fci" | "faie";
  total_slots: number;
  occupied_count: number;
  available_count: number;
  slots: ParkingSlotDto[];
  updated_at?: string;
  source?: VideoSnapshotSource | VideoSamplesSource;
}

export interface VideoSampleSlotDto {
  slot_id: string;
  occupied_frames: number;
  sample_count: number;
  occupancy_ratio: number;
  occupied: boolean;
}

export interface VideoSampleStatus {
  frame_index: number;
  total_slots: number;
  occupied_count: number;
  available_count: number;
  slots: ParkingSlotDto[];
}

export interface VideoSamplesResponse {
  location_id: "fci" | "faie";
  source: VideoSamplesSource;
  summary: {
    total_slots: number;
    occupied_count: number;
    available_count: number;
    sample_count: number;
    latest_frame_index: number;
    slots: VideoSampleSlotDto[];
  };
  samples: VideoSampleStatus[];
}
