import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRecentSearches,
  clearRecentSearches,
  deleteRecentSearch,
} from '@/lib/api/search';
import type { SearchHistory } from '@/lib/types/search';

export function useRecentSearches() {
  const queryClient = useQueryClient();

  // Query for recent searches
  const query = useQuery<SearchHistory[]>({
    queryKey: ['recent-searches'],
    queryFn: getRecentSearches,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
  });

  // Mutation to clear all recent searches
  const clearAll = useMutation({
    mutationFn: clearRecentSearches,
    onMutate: async () => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['recent-searches'] });

      // Snapshot previous value for rollback
      const previousSearches = queryClient.getQueryData<SearchHistory[]>([
        'recent-searches',
      ]);

      // Optimistically update to empty array
      queryClient.setQueryData<SearchHistory[]>(['recent-searches'], []);

      return { previousSearches };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      if (context?.previousSearches) {
        queryClient.setQueryData(['recent-searches'], context.previousSearches);
      }
    },
    onSettled: () => {
      // Refetch after mutation completes
      queryClient.invalidateQueries({ queryKey: ['recent-searches'] });
    },
  });

  // Mutation to remove a single search entry
  const removeOne = useMutation({
    mutationFn: deleteRecentSearch,
    onMutate: async (searchId: number) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['recent-searches'] });

      // Snapshot previous value for rollback
      const previousSearches = queryClient.getQueryData<SearchHistory[]>([
        'recent-searches',
      ]);

      // Optimistically remove the item
      queryClient.setQueryData<SearchHistory[]>(
        ['recent-searches'],
        (old) => old?.filter((s) => s.id !== searchId) ?? []
      );

      return { previousSearches };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      if (context?.previousSearches) {
        queryClient.setQueryData(['recent-searches'], context.previousSearches);
      }
    },
    onSettled: () => {
      // Refetch after mutation completes
      queryClient.invalidateQueries({ queryKey: ['recent-searches'] });
    },
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    clearAll: clearAll.mutate,
    removeOne: removeOne.mutate,
  };
}
