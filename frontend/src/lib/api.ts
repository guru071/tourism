/**
 * Centralized API client for the Aventis Platform.
 * Reads NEXT_PUBLIC_API_URL from environment.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
export const SERVER_ROOT = API_BASE.replace('/api/v1', '');

// ─── Types ──────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  message?: string;
  version?: string;
  timestamp?: string;
  services?: { database?: string; redis?: string };
}

export interface ApiRootResponse {
  message: string;
  status: string;
  modules?: string[];
}

export interface Destination {
  id: string;
  name: string;
  country: string;
  city?: string;
  region?: string;
  category?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  image_urls: string[];
  tags: string[];
  is_active: boolean;
  slug: string;
  avg_rating?: number;
  review_count?: number;
}

export interface DestinationList {
  items: Destination[];
  total: number;
  limit: number;
  offset: number;
}

export interface Activity {
  time_of_day: string;
  title: string;
  description: string;
  location?: string;
  duration_hours: number;
  estimated_cost_usd: number;
  category: string;
}

export interface DayPlan {
  day: number;
  theme: string;
  activities: Activity[];
  total_estimated_cost_usd: number;
  tips?: string;
}

export interface Itinerary {
  id: string;
  destination_id: string;
  destination_name?: string;
  duration_days: number;
  travel_style: string;
  budget_level: string;
  title: string;
  summary?: string;
  day_plans: DayPlan[];
  total_estimated_cost_usd: number;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  phone_number?: string;
  preferred_language: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

// ─── Error Handling ──────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options?.headers,
  };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || 'API request failed');
  }
  return res.json() as Promise<T>;
}

// ─── Health ──────────────────────────────────────────────────────────────────

export function getApiBaseUrl() { return API_BASE; }
export function getServerRootUrl() { return SERVER_ROOT; }

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>(`${SERVER_ROOT}/health`);
}

export async function fetchApiRoot(): Promise<ApiRootResponse> {
  return apiFetch<ApiRootResponse>('');
}

// ─── Destinations ────────────────────────────────────────────────────────────

export interface DestinationFilters {
  q?: string;
  category?: string;
  country?: string;
  min_rating?: number;
  limit?: number;
  offset?: number;
}

export async function fetchDestinations(filters: DestinationFilters = {}): Promise<DestinationList> {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.category) params.set('category', filters.category);
  if (filters.country) params.set('country', filters.country);
  if (filters.min_rating !== undefined) params.set('min_rating', String(filters.min_rating));
  if (filters.limit) params.set('limit', String(filters.limit));
  if (filters.offset) params.set('offset', String(filters.offset));
  const qs = params.toString();
  return apiFetch<DestinationList>(`/destinations${qs ? `?${qs}` : ''}`);
}

export async function fetchDestination(id: string): Promise<Destination> {
  return apiFetch<Destination>(`/destinations/${id}`);
}

export async function createDestination(data: Partial<Destination>): Promise<Destination> {
  return apiFetch<Destination>('/destinations', { method: 'POST', body: JSON.stringify(data) });
}

// ─── Itineraries ─────────────────────────────────────────────────────────────

export interface GenerateItineraryRequest {
  destination_id: string;
  duration_days: number;
  travel_style: string;
  budget_level: string;
  notes?: string;
}

export async function generateItinerary(req: GenerateItineraryRequest): Promise<Itinerary> {
  return apiFetch<Itinerary>('/itineraries/generate', { method: 'POST', body: JSON.stringify(req) });
}

export async function fetchItinerary(id: string): Promise<Itinerary> {
  return apiFetch<Itinerary>(`/itineraries/${id}`);
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function register(email: string, password: string, full_name: string, role: string): Promise<AuthToken> {
  return apiFetch<AuthToken>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name, role }),
  });
}

export async function login(email: string, password: string): Promise<AuthToken> {
  return apiFetch<AuthToken>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<User> {
  return apiFetch<User>('/auth/me');
}

// ─── Control Tower ───────────────────────────────────────────────────────────

export async function fetchDashboard() {
  return apiFetch<Record<string, unknown>>('/control-tower/dashboard');
}

export async function fetchCongestion() {
  return apiFetch<unknown[]>('/control-tower/congestion');
}

export async function fetchRevenue() {
  return apiFetch<unknown[]>('/control-tower/revenue');
}

export async function fetchUsers() {
  return apiFetch<User[]>('/users');
}

export async function updateUserRole(userId: string, role: string) {
  return apiFetch<Record<string, unknown>>(`/users/${userId}/role`, { method: 'PATCH', body: JSON.stringify({ role }) });
}

export async function updateUserStatus(userId: string, isActive: boolean) {
  return apiFetch<Record<string, unknown>>(`/users/${userId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) });
}

export async function verifyOperator(operatorId: string, status: string) {
  return apiFetch<Record<string, unknown>>(`/operators/${operatorId}/verify`, { method: 'PATCH', body: JSON.stringify({ status }) });
}

// ─── Partners & Listings ─────────────────────────────────────────────────────

export interface Listing {
  id: string;
  operator_id: string;
  destination_id: string;
  title: string;
  category: string;
  description: string;
  base_price: number;
  currency: string;
  availability: boolean;
  capacity?: number | null;
  duration_hours?: number | null;
  images?: string[];
  amenities?: string[];
  rating_average?: number;
  review_count?: number;
}

export async function fetchListings(destination_id?: string): Promise<Listing[]> {
  const query = destination_id ? `?destination_id=${encodeURIComponent(destination_id)}` : '';
  return apiFetch<Listing[]>(`/listings${query}`);
}

export async function fetchListing(listing_id: string): Promise<Listing> {
  return apiFetch<Listing>(`/listings/${listing_id}`);
}

export async function getMyOperator() {
  return apiFetch<Record<string, unknown>>('/operators/my');
}

export interface CreateListingPayload {
  destination_id: string;
  title: string;
  category: string;
  description: string;
  base_price: number;
  currency: string;
  capacity?: number;
  duration_hours?: number;
  latitude?: number;
  longitude?: number;
  location?: string;
  images?: string[];
  amenities?: string[];
}

export async function createListing(data: CreateListingPayload) {
  return apiFetch<{ id: string; title: string; slug: string }>('/listings', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ─── Bookings & Payments ─────────────────────────────────────────────────────

export interface Booking {
  id: string;
  booking_reference: string;
  status: string;
  listing_title?: string;
  listing_id?: string;
  start_date: string;
  end_date: string;
  guests_count: number;
  total_price: number;
  currency: string;
}

export interface CreateBookingOptions {
  check_in_date?: string;
  check_out_date?: string;
  num_guests?: number;
  special_requests?: string;
}

export async function createBooking(
  listing_id: string,
  options?: CreateBookingOptions | string,
  check_out_date?: string,
  num_guests: number = 1,
  special_requests?: string
): Promise<Booking> {
  let checkIn = '';
  let checkOut = '';
  let guests = 1;
  let requests: string | undefined;

  if (typeof options === 'object' && options !== null) {
    checkIn = options.check_in_date || '';
    checkOut = options.check_out_date || '';
    guests = options.num_guests ?? 1;
    requests = options.special_requests;
  } else if (typeof options === 'string') {
    checkIn = options;
    checkOut = check_out_date || '';
    guests = num_guests;
    requests = special_requests;
  }

  if (!checkIn) {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    checkIn = d.toISOString().split('T')[0];
  }
  if (!checkOut) {
    const d = new Date(checkIn);
    d.setDate(d.getDate() + 2);
    checkOut = d.toISOString().split('T')[0];
  }

  return apiFetch<Booking>('/bookings', {
    method: 'POST',
    body: JSON.stringify({
      listing_id,
      check_in_date: checkIn,
      check_out_date: checkOut,
      num_guests: guests,
      special_requests: requests,
    }),
  });
}

export async function getOperatorBookings(operatorId: string) {
  return apiFetch<Booking[]>(`/bookings?operator_id=${operatorId}`);
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export async function createCheckoutSession(booking_id: string): Promise<CheckoutSessionResponse> {
  return apiFetch<CheckoutSessionResponse>('/payments/create-checkout-session', {
    method: 'POST',
    body: JSON.stringify({ booking_id }),
  });
}

// ─── Chat Assistant ──────────────────────────────────────────────────────────

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export async function sendChatMessage(
  message: string,
  history: ChatMessage[] = []
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  });
}
