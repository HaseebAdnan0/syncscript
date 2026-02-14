'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import SearchInput from '@/components/features/search/SearchInput';
import SearchTypeFilter from '@/components/features/search/SearchTypeFilter';
import { SearchResultsList } from '@/components/features/search/SearchResultsList';
import SearchResultsSkeleton from '@/components/features/search/SearchResultsSkeleton';
import NoResultsState from '@/components/features/search/NoResultsState';
import { useSearchQuery } from '@/hooks/useSearchQuery';
import type { SearchResultType } from '@/lib/types/search';

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

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Read initial query from URL
  const initialQuery = searchParams.get('q') || '';
  const initialType = (searchParams.get('type') as FilterType) || 'all';

  const [query, setQuery] = useState(initialQuery);
  const [selectedType, setSelectedType] = useState<FilterType>(initialType);

  // Update URL when query or type changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (query) {
      params.set('q', query);
    }
    if (selectedType !== 'all') {
      params.set('type', selectedType);
    }

    const newUrl = params.toString() ? `/search?${params.toString()}` : '/search';
    router.replace(newUrl);
  }, [query, selectedType, router]);

  // Search query with type filter
  const apiType = filterToApiType(selectedType);
  const filters = apiType ? { type: apiType } : undefined;
  const { data: searchResults, isLoading } = useSearchQuery({ query, filters });

  // Handle clear input
  const handleClearInput = () => {
    setQuery('');
    setSelectedType('all');
  };

  // Handle type change
  const handleTypeChange = (newType: FilterType) => {
    setSelectedType(newType);
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
  const hasResults = searchResults && searchResults.total_count > 0;

  return (
    <div className="min-h-screen bg-[#030304] p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 font-heading">
            Search
          </h1>
          <p className="text-white/60">
            Search across all your vaults, sources, and annotations
          </p>
        </div>

        {/* Search Input */}
        <div className="mb-6">
          <SearchInput
            value={query}
            onChange={setQuery}
            onClear={handleClearInput}
            autoFocus
          />
        </div>

        {/* Type Filter */}
        {(hasResults || isLoading) && query.length >= 2 && (
          <div className="mb-6">
            <SearchTypeFilter
              activeType={selectedType}
              onTypeChange={handleTypeChange}
              resultCounts={resultCounts}
            />
          </div>
        )}

        {/* Results Area */}
        <div className="min-h-[400px]">
          {/* Show loading skeleton while searching */}
          {query.length >= 2 && isLoading && <SearchResultsSkeleton />}

          {/* Show results when available */}
          {query.length >= 2 && !isLoading && hasResults && (
            <SearchResultsList results={searchResults} onResultClick={() => {}} />
          )}

          {/* Show no results state */}
          {query.length >= 2 && !isLoading && !hasResults && (
            <NoResultsState query={query} />
          )}

          {/* Show prompt for minimum query length or empty state */}
          {query.length === 0 && (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-white/40"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white/80 mb-2">
                Start searching
              </h3>
              <p className="text-white/40 text-sm max-w-md">
                Enter at least 2 characters to search across your vaults, sources, and annotations
              </p>
            </div>
          )}

          {query.length === 1 && (
            <div className="py-12 text-center text-white/40 text-sm">
              Type at least 2 characters to search...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[#030304]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/20 border-t-[#F7931A]" />
          <p className="text-sm text-white/60">Loading search...</p>
        </div>
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
}
