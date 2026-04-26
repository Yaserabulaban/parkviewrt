import type { ParkingLayoutConfig } from '@/types/layout';

export const parkingLayouts: Record<'fci' | 'faie', ParkingLayoutConfig> = {
  fci: {
    locationId: 'fci',
    title: 'FCI Parking',
    rows: [
      {
        rowLabel: 'Row A',
        slots: [
          { slotId: 'A1', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A2', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A3', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A4', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A5', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A6', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A7', rowLabel: 'Row A', shape: 'angled-left' },
          { slotId: 'A8', rowLabel: 'Row A', shape: 'angled-left' }
        ]
      },
      {
        rowLabel: 'Row F',
        slots: [
          { slotId: 'F1', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F2', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F3', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F4', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F5', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F6', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F7', rowLabel: 'Row F', shape: 'angled-right' },
          { slotId: 'F8', rowLabel: 'Row F', shape: 'angled-right' }
        ]
      }
    ]
  },

  faie: {
    locationId: 'faie',
    title: 'FAIE Parking',
    rows: [
      {
        rowLabel: 'Row B',
        slots: [
          { slotId: 'B1', rowLabel: 'Row B', shape: 'perpendicular' },
          { slotId: 'B2', rowLabel: 'Row B', shape: 'perpendicular' },
          { slotId: 'B3', rowLabel: 'Row B', shape: 'perpendicular' },
          { slotId: 'B4', rowLabel: 'Row B', shape: 'perpendicular' },
          { slotId: 'B5', rowLabel: 'Row B', shape: 'perpendicular' },
          { slotId: 'B6', rowLabel: 'Row B', shape: 'perpendicular' }
        ]
      },
      {
        rowLabel: 'Row D',
        slots: [
          { slotId: 'D1', rowLabel: 'Row D', shape: 'perpendicular' },
          { slotId: 'D2', rowLabel: 'Row D', shape: 'perpendicular' },
          { slotId: 'D3', rowLabel: 'Row D', shape: 'perpendicular' },
          { slotId: 'D4', rowLabel: 'Row D', shape: 'perpendicular' },
          { slotId: 'D5', rowLabel: 'Row D', shape: 'perpendicular' },
          { slotId: 'D6', rowLabel: 'Row D', shape: 'perpendicular' }
        ]
      },
      {
        rowLabel: 'Row E',
        slots: [
          { slotId: 'E1', rowLabel: 'Row E', shape: 'perpendicular' },
          { slotId: 'E2', rowLabel: 'Row E', shape: 'perpendicular' },
          { slotId: 'E3', rowLabel: 'Row E', shape: 'perpendicular' },
          { slotId: 'E4', rowLabel: 'Row E', shape: 'perpendicular' },
          { slotId: 'E5', rowLabel: 'Row E', shape: 'perpendicular' },
          { slotId: 'E6', rowLabel: 'Row E', shape: 'perpendicular' }
        ]
      }
    ]
  }
};