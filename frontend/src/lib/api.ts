/**
 * API client for MedFlow Integration API.
 *
 * All API calls go through this module for consistent
 * base URL handling and error management.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  return response.json();
}

// --- Leads ---

export interface Lead {
  id: string;
  name?: { firstName?: string; lastName?: string };
  phones?: { primaryPhoneNumber?: string };
  emails?: { primaryEmail?: string };
  stage?: string;
  origem?: string;
  createdAt?: string;
}

export interface LeadsResponse {
  data: Lead[];
  total: number;
  limite: number;
  offset: number;
}

export async function fetchLeads(params?: {
  etapa?: string;
  origem?: string;
  limite?: number;
  offset?: number;
}): Promise<LeadsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.etapa) searchParams.set("etapa", params.etapa);
  if (params?.origem) searchParams.set("origem", params.origem);
  if (params?.limite) searchParams.set("limite", String(params.limite));
  if (params?.offset) searchParams.set("offset", String(params.offset));

  const qs = searchParams.toString();
  return request<LeadsResponse>(`/leads${qs ? `?${qs}` : ""}`);
}

export async function searchLead(telefone: string): Promise<{ data: Lead }> {
  return request<{ data: Lead }>(`/leads/search?telefone=${encodeURIComponent(telefone)}`);
}

// --- Bookings ---

export interface Booking {
  id?: number;
  uid?: string;
  titulo?: string;
  inicio?: string;
  fim?: string;
  status?: string;
  attendees?: Array<{ nome?: string; email?: string }>;
  metadata?: Record<string, unknown>;
}

export interface BookingsResponse {
  data: Booking[];
  total: number;
}

export async function fetchBookings(params?: {
  data_inicio?: string;
  data_fim?: string;
  status?: string;
}): Promise<BookingsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.data_inicio) searchParams.set("data_inicio", params.data_inicio);
  if (params?.data_fim) searchParams.set("data_fim", params.data_fim);
  if (params?.status) searchParams.set("status", params.status);

  const qs = searchParams.toString();
  return request<BookingsResponse>(`/bookings${qs ? `?${qs}` : ""}`);
}

export async function fetchAvailability(params?: {
  data?: string;
  event_type_id?: number;
}): Promise<{ data: Array<{ data: string; inicio: string; disponivel: boolean }> }> {
  const searchParams = new URLSearchParams();
  if (params?.data) searchParams.set("data", params.data);
  if (params?.event_type_id) searchParams.set("event_type_id", String(params.event_type_id));

  const qs = searchParams.toString();
  return request(`/bookings/availability${qs ? `?${qs}` : ""}`);
}

// --- Conversations ---

export interface Conversation {
  id: number;
  status?: string;
  inbox_id?: number;
  contact?: { id: number; name?: string; phone_number?: string };
  messages_count?: number;
  created_at?: string;
  last_activity_at?: string;
  labels?: string[];
}

export async function fetchConversations(params?: {
  status?: string;
  page?: number;
}): Promise<{ data: Conversation[]; meta: Record<string, unknown> }> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.page) searchParams.set("page", String(params.page));

  const qs = searchParams.toString();
  return request(`/conversations${qs ? `?${qs}` : ""}`);
}

export async function fetchConversationStats(): Promise<{
  open: number;
  pending: number;
  bot_handling: number;
}> {
  return request("/conversations/stats");
}

// --- Dashboard ---

export interface DashboardMetrics {
  leads_total: number;
  bookings_upcoming: number;
  conversations_active: number;
  conversion_rate: number;
  period: { start: string; end: string };
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  return request<DashboardMetrics>("/dashboard/metrics");
}

export async function fetchRecentLeads(): Promise<{ data: Lead[] }> {
  return request<{ data: Lead[] }>("/dashboard/recent-leads");
}

export async function fetchUpcomingBookings(): Promise<{ data: Booking[] }> {
  return request<{ data: Booking[] }>("/dashboard/upcoming-bookings");
}
