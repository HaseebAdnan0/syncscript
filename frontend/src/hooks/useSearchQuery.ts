import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { search } from '@/lib/api/search';
import type { SearchResponse, SearchFilters } from '@/lib/types/search';

interface UseSearchQueryOptions {
  query: string;
  filters?: SearchFilters;
}

export function useSearchQuery({ query, filters }: UseSearchQueryOptions) {
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce query by 200ms
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, 200);

    return () => {
      clearTimeout(handler);
    };
  }, [query]);

  return useQuery<SearchResponse>({
    queryKey: ['search', debouncedQuery, filters],
    queryFn: () => search(debouncedQuery, filters),
    enabled: debouncedQuery.length >= 2,
    staleTime: 30 * 1000, // 30 seconds
  });
}
