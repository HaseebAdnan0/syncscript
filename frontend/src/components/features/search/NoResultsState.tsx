import React from 'react';
import { Search } from 'lucide-react';

interface NoResultsStateProps {
  query: string;
  popularSearches?: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

export default function NoResultsState({
  query,
  popularSearches = [],
  onSuggestionClick
}: NoResultsStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Icon */}
      <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6">
        <Search className="w-8 h-8 text-white/40" />
      </div>

      {/* Main message */}
      <h3 className="text-xl font-heading text-white mb-2">
        No results for &quot;{query}&quot;
      </h3>

      {/* Suggestions */}
      <div className="text-center space-y-2 mb-6">
        <p className="text-white/60">
          Try different keywords or search in all types
        </p>
        <p className="text-white/60 text-sm">
          Check your spelling or use more general terms
        </p>
      </div>

      {/* Popular searches */}
      {popularSearches.length > 0 && (
        <div className="mt-8 w-full max-w-md">
          <p className="text-sm text-white/40 uppercase tracking-wider mb-3">
            Popular searches
          </p>
          <div className="flex flex-wrap gap-2">
            {popularSearches.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => onSuggestionClick?.(suggestion)}
                className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-white/80 text-sm hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
