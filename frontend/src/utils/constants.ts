import type { BookingStatus, Role, SlotStatus } from '@/types';

export const ROLES: Record<Role, Role> = {
  saas_admin: 'saas_admin',
  turf_owner: 'turf_owner',
  player: 'player',
};

export const SLOT_STATUS_LABELS: Record<SlotStatus, string> = {
  available: 'Available',
  booked: 'Booked',
  blocked: 'Blocked',
  maintenance: 'Maintenance',
};

export const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  pending_payment: 'Pending Payment',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
  completed: 'Completed',
  no_show: 'No Show',
};

export const PLATFORM_CONVENIENCE_FEE_PER_HOUR = 20;

export const COMMON_AMENITIES = [
  'parking',
  'washroom',
  'changing_room',
  'floodlights',
  'drinking_water',
  'cafeteria',
  'first_aid',
] as const;

export const ACCESS_TOKEN_KEY = 'turf_access_token';
