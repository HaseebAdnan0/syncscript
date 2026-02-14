'use client';

import { FolderOpen, FileText, StickyNote } from 'lucide-react';
import type { SearchResult } from '@/lib/types/search';

interface SearchResultItemProps {
  result: SearchResult;
  onClick?: () => void;
}

// Icon mapping for different result types
const typeIcons = {
  vault: FolderOpen,
  source: FileText,
  annotation: StickyNote,
} as const;

export default function SearchResultItem({ result, onClick }: SearchResultItemProps) {
  const Icon = typeIcons[result.type];

  // Parse highlighted text - replace <mark> tags with styled spans
  const renderHighlightedText = (text: string) => {
    // Split by <mark> and </mark> tags
    const parts = text.split(/(<mark>|<\/mark>)/g);
    let isHighlighted = false;

    return (
      <>
        {parts.map((part, index) => {
          if (part === '<mark>') {
            isHighlighted = true;
            return null;
          }
          if (part === '</mark>') {
            isHighlighted = false;
            return null;
          }
          if (!part) return null;

          return (
            <span
              key={index}
              className={isHighlighted ? 'bg-[#F7931A] text-black px-1 rounded' : ''}
            >
              {part}
            </span>
          );
        })}
      </>
    );
  };

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 rounded-lg hover:bg-white/5 transition-colors group"
    >
      <div className="flex items-start gap-3">
        {/* Type icon */}
        <div className="text-[#F7931A] mt-1 flex-shrink-0">
          <Icon className="h-5 w-5" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Title with highlights */}
          <div className="text-white font-medium mb-1 text-base">
            {renderHighlightedText(result.highlight || result.title)}
          </div>

          {/* Breadcrumb for context */}
          {result.breadcrumb && (
            <div className="text-white/50 text-xs mb-2">
              {result.breadcrumb}
            </div>
          )}

          {/* Preview snippet with highlighted text */}
          {result.snippet && (
            <div className="text-white/70 text-sm line-clamp-2">
              {renderHighlightedText(result.snippet)}
            </div>
          )}
        </div>

        {/* Relevance score (subtle indicator) */}
        <div className="text-white/30 text-xs mt-1 flex-shrink-0">
          {(result.relevance * 100).toFixed(0)}%
        </div>
      </div>
    </button>
  );
}
