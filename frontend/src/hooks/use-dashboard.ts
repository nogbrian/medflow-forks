"use client";

import { useApi } from "./use-api";
import {
  fetchDashboardMetrics,
  fetchRecentLeads,
  fetchUpcomingBookings,
  type DashboardMetrics,
  type Lead,
  type Booking,
} from "@/lib/api";

/**
 * Hook for dashboard metrics (leads, bookings, conversations, conversion rate).
 */
export function useDashboardMetrics() {
  return useApi<DashboardMetrics>(fetchDashboardMetrics);
}

/**
 * Hook for recent leads table on dashboard.
 */
export function useRecentLeads() {
  return useApi<{ data: Lead[] }>(fetchRecentLeads);
}

/**
 * Hook for upcoming bookings sidebar on dashboard.
 */
export function useUpcomingBookings() {
  return useApi<{ data: Booking[] }>(fetchUpcomingBookings);
}
