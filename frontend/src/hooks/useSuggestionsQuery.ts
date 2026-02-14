import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { getSuggestions } from '@/lib/api/search';
import type { SearchSuggestion } from '@/lib/types/search';

export function useSuggestionsQuery(query: string) {
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce query by 150ms (faster than full search for better UX)
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, 150);

    return () => {
      clearTimeout(handler);
    };
  }, [query]);

  return useQuery<SearchSuggestion[]>({
    queryKey: ['search-suggestions', debouncedQuery],
    queryFn: () => getSuggestions(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 60 * 1000, // 1 minute (suggestions change less frequently)
  });
}
