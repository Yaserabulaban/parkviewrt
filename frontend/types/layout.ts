export type ParkingLocationId = 'fci' | 'faie';

export type SlotShape = 'angled-left' | 'angled-right' | 'perpendicular';

export interface LayoutSlot {
  slotId: string;
  rowLabel: string;
  shape: SlotShape;
}

export interface ParkingLayoutConfig {
  locationId: ParkingLocationId;
  title: string;
  rows: {
    rowLabel: string;
    slots: LayoutSlot[];
  }[];
}