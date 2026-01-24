"use client";

import { useEffect, useState } from "react";
import { getStoredToken } from "@/lib/auth";

type ServiceName = "chatwoot" | "twenty" | "calcom";

interface UseSsoUrlResult {
  url: string | null;
  loading: boolean;
  error: boolean;
}

/**
 * Fetches an SSO-authenticated URL for an embedded service.
 * Falls back to the provided base URL if SSO is unavailable.
 */
export function useSsoUrl(service: ServiceName, fallbackUrl: string): UseSsoUrlResult {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchSsoUrl() {
      const token = getStoredToken();
      if (!token) {
        if (!cancelled) {
          setUrl(fallbackUrl);
          setLoading(false);
        }
        return;
      }

      try {
        const response = await fetch(`/api/sso/${service}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (cancelled) return;

        if (response.ok) {
          const data = await response.json();
          setUrl(data.url);
        } else {
          setError(true);
          setUrl(fallbackUrl);
        }
      } catch {
        if (!cancelled) {
          setError(true);
          setUrl(fallbackUrl);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchSsoUrl();
    return () => { cancelled = true; };
  }, [service, fallbackUrl]);

  return { url, loading, error };
}
