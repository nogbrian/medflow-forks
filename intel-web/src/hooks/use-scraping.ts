import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { triggerScrape, getScrapeStatus } from '@/lib/api';
import { PROFILES_KEY } from './use-profiles';

export const SCRAPE_RUN_KEY = ['scrape-run'] as const;

export function useTriggerScrape() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: triggerScrape,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
    },
  });
}

export function useScrapeStatus(
  scrapeRunId: string | undefined,
  options: { enabled?: boolean; refetchInterval?: number } = {}
) {
  return useQuery({
    queryKey: [...SCRAPE_RUN_KEY, scrapeRunId],
    queryFn: () => getScrapeStatus(scrapeRunId!),
    enabled: !!scrapeRunId && options.enabled !== false,
    refetchInterval: (query) => {
      const data = query.state.data as { status?: string } | undefined;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return options.refetchInterval || 3000;
    },
  });
}
