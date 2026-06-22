export type Role = 'saas_admin' | 'turf_owner' | 'player';

export type SlotStatus = 'available' | 'booked' | 'blocked' | 'maintenance';

export type BookingStatus =
  | 'pending_payment'
  | 'confirmed'
  | 'cancelled'
  | 'completed'
  | 'no_show';

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error: ApiError | null;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{ field: string; message: string }>;
}

export interface User {
  id: string;
  email: string;
  phone: string;
  role: Role;
  is_active: boolean;
  is_verified: boolean;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface TurfSportView {
  id: string;
  sport_id: string;
  sport_name: string;
  icon_url: string | null;
  price_per_hour: number;
  advance_deposit_percentage: number;
  min_players: number;
  max_players: number;
  default_duration_minutes: number;
}

export interface DayHours {
  open: string;
  close: string;
}

export type OperatingHours = Partial<Record<string, DayHours>>;

export interface TurfCard {
  id: string;
  name: string;
  address: string;
  city: string;
  latitude: number | null;
  longitude: number | null;
  description: string | null;
  amenities: string[];
  images: string[];
  sports: TurfSportView[];
  min_price_per_hour: number | null;
  distance_km: number | null;
}

export interface TurfDetail extends TurfCard {
  operating_hours: OperatingHours;
}

export interface Slot {
  id: string;
  turf_sport_id: string;
  slot_date: string;
  start_time: string;
  end_time: string;
  status: SlotStatus;
}

export interface DiscoveryResult {
  items: TurfCard[];
  total: number;
  page: number;
  limit: number;
}

export interface SportSummary {
  name: string;
  icon_url: string | null;
}

export interface Booking {
  id: string;
  booking_code: string;
  turf_sport_id: string;
  slot_ids: string[];
  booking_date: string;
  total_amount: number;
  advance_deposit_amount: number;
  platform_fee: number;
  owner_payout_amount: number;
  status: BookingStatus;
  payment_status: string;
  razorpay_order_id: string | null;
  razorpay_payment_id: string | null;
  refund_status: string | null;
  refund_amount: number | null;
  created_at: string;
}

export interface BookingCreateResponse {
  booking_id: string;
  booking_code: string;
  razorpay_order_id: string;
  amount: number;
  currency: 'INR';
}

export interface DiscoveryFilters {
  city?: string;
  sport?: string;
  price_min?: number;
  price_max?: number;
  amenities?: string[];
  date?: string;
  page?: number;
  limit?: number;
}

export interface SportBreakdown {
  sport: string;
  bookings: number;
  revenue: number;
}

export interface OwnerAnalytics {
  total_bookings: number;
  total_revenue: number;
  total_platform_fees: number;
  total_owner_payouts: number;
  by_sport: SportBreakdown[];
  time_series: Array<{ date: string; bookings: number; revenue: number }>;
}

export interface AdminAnalytics {
  total_bookings: number;
  total_revenue: number;
  total_platform_fees: number;
  total_owner_payouts: number;
  active_owners: number;
  active_players: number;
  time_series: Array<{ date: string; bookings: number; platform_fees: number }>;
}

export interface AdminUser {
  id: string;
  email: string;
  phone: string;
  role: Role;
  is_active: boolean;
  is_verified: boolean;
  name: string | null;
  created_at: string | null;
}

export interface Payout {
  id: string;
  tenant_id: string;
  booking_id: string;
  amount: number;
  status: string;
  razorpay_transfer_id: string | null;
  created_at: string | null;
}

export interface OwnerTurf extends TurfDetail {
  is_active: boolean;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
