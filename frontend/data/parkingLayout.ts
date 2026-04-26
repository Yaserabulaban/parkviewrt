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
        rowLabel: 'Row B',
        slots: [
          { slotId: 'B1', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B2', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B3', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B4', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B5', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B6', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B7', rowLabel: 'Row B', shape: 'angled-right' },
          { slotId: 'B8', rowLabel: 'Row B', shape: 'angled-right' }
        ]
      }
    ]
  },

  faie: {
    locationId: 'faie',
    title: 'FAIE Parking',
    rows: [
      {
        rowLabel: 'Row C',
        slots: [
          { slotId: 'C1', rowLabel: 'Row C', shape: 'perpendicular' },
          { slotId: 'C2', rowLabel: 'Row C', shape: 'perpendicular' },
          { slotId: 'C3', rowLabel: 'Row C', shape: 'perpendicular' },
          { slotId: 'C4', rowLabel: 'Row C', shape: 'perpendicular' },
          { slotId: 'C5', rowLabel: 'Row C', shape: 'perpendicular' },
          { slotId: 'C6', rowLabel: 'Row C', shape: 'perpendicular' }
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