export type SlotStatus = "occupied" | "empty";

export interface ParkingSlotDto {
  slot_id: string;
  occupied: boolean;
}

export interface ParkingStatusResponse {
  location_id: "fci" | "faie";
  total_slots: number;
  occupied_count: number;
  available_count: number;
  slots: ParkingSlotDto[];
  updated_at?: string;
}