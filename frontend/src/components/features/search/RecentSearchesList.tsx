'use client';

import { Clock, X } from 'lucide-react';
import type { SearchHistory } from '@/lib/types/search';

interface RecentSearchesListProps {
  searches: SearchHistory[];
  onSearchClick: (query: string) => void;
  onClearAll: () => void;
  onRemove: (id: number) => void;
}

export default function RecentSearchesList({
  searches,
  onSearchClick,
  onClearAll,
  onRemove,
}: RecentSearchesListProps) {
  if (!searches || searches.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between px-4">
        <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
          Recent Searches
        </h3>
        <button
          onClick={onClearAll}
          className="text-xs text-white/60 hover:text-[#F7931A] transition-colors"
        >
          Clear all
        </button>
      </div>

      {/* Recent searches list */}
      <div className="space-y-1">
        {searches.map((search) => (
          <div
            key={search.id}
            className="group flex items-center justify-between px-4 py-2.5 hover:bg-white/5 rounded-lg transition-all cursor-pointer"
            onClick={() => onSearchClick(search.query)}
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <Clock className="w-4 h-4 text-white/40 flex-shrink-0" />
              <span className="text-sm text-white/90 truncate">
                {search.query}
              </span>
              {search.result_count > 0 && (
                <span className="text-xs text-white/50 flex-shrink-0">
                  {search.result_count} result{search.result_count !== 1 ? 's' : ''}
                </span>
              )}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove(search.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-all"
              aria-label="Remove search"
            >
              <X className="w-3.5 h-3.5 text-white/60 hover:text-[#F7931A]" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
