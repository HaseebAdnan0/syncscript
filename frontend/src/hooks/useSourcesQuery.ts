// React Query hook for fetching sources

import { useQuery } from '@tanstack/react-query';
import { getSources } from '@/lib/api/sources';
import type { SourcesFilterParams } from '@/lib/types/sources';

interface UseSourcesQueryParams {
  vaultId: number;
  filters?: SourcesFilterParams;
}

/**
 * Hook to fetch sources for a vault with optional filters
 *
 * @param vaultId - The ID of the vault to fetch sources for
 * @param filters - Optional filter parameters (type, dateFrom, dateTo, contributor, search)
 * @returns React Query result with sources data, loading state, error, and refetch function
 */
export function useSourcesQuery({ vaultId, filters }: UseSourcesQueryParams) {
  return useQuery({
    queryKey: ['sources', vaultId, filters],
    queryFn: () => getSources(vaultId, filters),
    enabled: !!vaultId,
    staleTime: 30 * 1000, // 30 seconds
  });
}
