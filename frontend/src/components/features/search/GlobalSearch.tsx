'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import GlobalSearchModal from './GlobalSearchModal';
import SearchInput from './SearchInput';
import SearchTypeFilter from './SearchTypeFilter';
import { SearchResultsList } from './SearchResultsList';
import SearchResultsSkeleton from './SearchResultsSkeleton';
import RecentSearchesList from './RecentSearchesList';
import NoResultsState from './NoResultsState';
import { useSearchQuery } from '@/hooks/useSearchQuery';
import { useRecentSearches } from '@/hooks/useRecentSearches';
import type { SearchResultType, SearchResult } from '@/lib/types/search';

// Map between plural filter types and singular API types
type FilterType = 'all' | 'vaults' | 'sources' | 'annotations';

const filterToApiType = (filter: FilterType): SearchResultType | undefined => {
  switch (filter) {
    case 'vaults': return 'vault';
    case 'sources': return 'source';
    case 'annotations': return 'annotation';
    default: return undefined;
  }
};

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function GlobalSearch({ isOpen, onClose }: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [selectedType, setSelectedType] = useState<FilterType>('all');
  const router = useRouter();

  // Search query with type filter (convert plural filter to singular API type)
  const apiType = filterToApiType(selectedType);
  const filters = apiType ? { type: apiType } : undefined;
  const { data: searchResults, isLoading } = useSearchQuery({ query, filters });

  // Recent searches
  const { data: recentSearches = [], clearAll, removeOne } = useRecentSearches();

  // Handle search from recent searches
  const handleRecentSearchClick = (searchQuery: string) => {
    setQuery(searchQuery);
  };

  // Handle clear input
  const handleClearInput = () => {
    setQuery('');
    setSelectedType('all');
  };

  // Handle result click - navigate to appropriate page
  const handleResultClick = (result: SearchResult) => {
    // Navigate based on result type
    switch (result.type) {
      case 'vault':
        router.push(`/vaults/${result.id}`);
        break;
      case 'source':
        router.push(`/vaults/${result.vault_id}/sources/${result.id}`);
        break;
      case 'annotation':
        // Navigate to source page with annotation highlighted
        router.push(`/vaults/${result.vault_id}/sources/${result.id}#annotation-${result.id}`);
        break;
    }
    // Close modal after navigation
    handleClose();
  };

  // Close modal and reset state
  const handleClose = () => {
    onClose();
    // Reset state after modal closes (with a small delay to avoid visual flicker)
    setTimeout(() => {
      setQuery('');
      setSelectedType('all');
    }, 200);
  };

  // Determine result counts for filter tabs
  const resultCounts = searchResults
    ? {
        vaults: searchResults.results.vaults?.length || 0,
        sources: searchResults.results.sources?.length || 0,
        annotations: searchResults.results.annotations?.length || 0,
      }
    : undefined;

  // Check if we have any results
  const hasResults =
    searchResults && searchResults.total_count > 0;

  return (
    <GlobalSearchModal isOpen={isOpen} onClose={handleClose}>
      <div className="space-y-4">
        {/* Search Input */}
        <SearchInput
          value={query}
          onChange={setQuery}
          onClear={handleClearInput}
          autoFocus
        />

        {/* Type Filter (only show when we have results or are loading) */}
        {(hasResults || isLoading) && query.length >= 2 && (
          <SearchTypeFilter
            activeType={selectedType}
            onTypeChange={setSelectedType}
            resultCounts={resultCounts}
          />
        )}

        {/* Results Area */}
        <div className="max-h-[500px] overflow-y-auto">
          {/* Show recent searches when input is empty */}
          {query.length === 0 && (
            <RecentSearchesList
              searches={recentSearches}
              onSearchClick={handleRecentSearchClick}
              onClearAll={clearAll}
              onRemove={removeOne}
            />
          )}

          {/* Show loading skeleton while searching */}
          {query.length >= 2 && isLoading && <SearchResultsSkeleton />}

          {/* Show results when available */}
          {query.length >= 2 && !isLoading && hasResults && (
            <SearchResultsList results={searchResults} onResultClick={handleResultClick} />
          )}

          {/* Show no results state */}
          {query.length >= 2 && !isLoading && !hasResults && (
            <NoResultsState query={query} />
          )}

          {/* Show prompt for minimum query length */}
          {query.length === 1 && (
            <div className="py-12 text-center text-white/40 text-sm">
              Type at least 2 characters to search...
            </div>
          )}
        </div>
      </div>
    </GlobalSearchModal>
  );
}
