import React from 'react';
import { SearchResultItem } from './SearchResultItem';
import type { SearchResponse } from '@/lib/types/search';

interface SearchResultsListProps {
  results: SearchResponse;
  onResultClick: (result: SearchResponse['results']['vaults'][0] | SearchResponse['results']['sources'][0] | SearchResponse['results']['annotations'][0]) => void;
}

export function SearchResultsList({ results, onResultClick }: SearchResultsListProps) {
  const { vaults, sources, annotations } = results.results;

  // Max results to show in quick view per section
  const MAX_QUICK_VIEW = 5;

  // Helper to determine if section should be shown
  const hasResults = (items: any[]) => items && items.length > 0;

  return (
    <div className="flex flex-col gap-6 max-h-[500px] overflow-y-auto px-2">
      {/* Vaults Section */}
      {hasResults(vaults) && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
              Vaults
            </h3>
            {vaults.length > MAX_QUICK_VIEW && (
              <button
                className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors"
                onClick={() => {/* Navigate to full search page with vaults filter */}}
              >
                See all {vaults.length} results →
              </button>
            )}
          </div>
          <div className="flex flex-col gap-1">
            {vaults.slice(0, MAX_QUICK_VIEW).map((vault) => (
              <SearchResultItem
                key={vault.id}
                result={vault}
                onClick={() => onResultClick(vault)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Sources Section */}
      {hasResults(sources) && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
              Sources
            </h3>
            {sources.length > MAX_QUICK_VIEW && (
              <button
                className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors"
                onClick={() => {/* Navigate to full search page with sources filter */}}
              >
                See all {sources.length} results →
              </button>
            )}
          </div>
          <div className="flex flex-col gap-1">
            {sources.slice(0, MAX_QUICK_VIEW).map((source) => (
              <SearchResultItem
                key={source.id}
                result={source}
                onClick={() => onResultClick(source)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Annotations Section */}
      {hasResults(annotations) && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
              Annotations
            </h3>
            {annotations.length > MAX_QUICK_VIEW && (
              <button
                className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors"
                onClick={() => {/* Navigate to full search page with annotations filter */}}
              >
                See all {annotations.length} results →
              </button>
            )}
          </div>
          <div className="flex flex-col gap-1">
            {annotations.slice(0, MAX_QUICK_VIEW).map((annotation) => (
              <SearchResultItem
                key={annotation.id}
                result={annotation}
                onClick={() => onResultClick(annotation)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
