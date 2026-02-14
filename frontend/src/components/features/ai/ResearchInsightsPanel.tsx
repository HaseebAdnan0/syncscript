'use client';

import { useState } from 'react';
import { RefreshCw, TrendingUp, AlertCircle, Link2, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface Theme {
  name: string;
  weight: number;
  source_count: number;
}

export interface CrossReference {
  sources: string[];
  connection: string;
}

export interface VaultInsights {
  themes: Theme[];
  research_gaps: string[];
  cross_references: CrossReference[];
  suggested_searches: string[];
  generated_at: string;
}

export interface ResearchInsightsPanelProps {
  insights: VaultInsights | null;
  onRefresh: () => void;
  sourceCount?: number;
  isLoading?: boolean;
  lastUpdated?: string;
}

export function ResearchInsightsPanel({
  insights,
  onRefresh,
  sourceCount = 0,
  isLoading = false,
  lastUpdated,
}: ResearchInsightsPanelProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('themes');

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // Empty state for vaults with < 2 sources
  if (sourceCount < 2) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-12 text-center">
        <div className="max-w-md mx-auto">
          <AlertCircle className="w-16 h-16 mx-auto mb-6 text-[#F7931A]/50" />
          <h3 className="text-2xl font-heading font-bold text-white mb-3">
            Not Enough Sources
          </h3>
          <p className="text-[#94A3B8] leading-relaxed">
            Add at least 2 sources to your vault to generate research insights.
            The AI will analyze themes, identify gaps, and suggest connections across your sources.
          </p>
        </div>
      </div>
    );
  }

  // Generate insights state
  if (!insights && !isLoading) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-12 text-center">
        <div className="max-w-md mx-auto">
          <TrendingUp className="w-16 h-16 mx-auto mb-6 text-[#F7931A]" />
          <h3 className="text-2xl font-heading font-bold text-white mb-3">
            Discover Research Insights
          </h3>
          <p className="text-[#94A3B8] mb-8 leading-relaxed">
            Let AI analyze your {sourceCount} sources to identify common themes, research gaps,
            cross-references, and suggested search directions.
          </p>
          <Button
            onClick={onRefresh}
            className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
          >
            Generate Insights
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            Research Insights
          </h2>
          {lastUpdated && (
            <p className="text-sm text-[#94A3B8] mt-1">
              Last updated: {new Date(lastUpdated).toLocaleDateString()} at{' '}
              {new Date(lastUpdated).toLocaleTimeString()}
            </p>
          )}
        </div>
        <Button
          onClick={onRefresh}
          disabled={isLoading}
          className="bg-[#0F1115] border border-white/20 text-white hover:border-[#F7931A] rounded-full px-4 py-2 transition-all"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Themes Section */}
      <div className="mb-6">
        <button
          onClick={() => toggleSection('themes')}
          className="w-full flex items-center justify-between p-4 bg-black/30 rounded-xl hover:bg-black/40 transition-all"
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-[#F7931A]" />
            <h3 className="text-lg font-heading font-bold text-white">
              Common Themes
            </h3>
          </div>
          <svg
            className={`w-5 h-5 text-[#94A3B8] transition-transform ${
              expandedSection === 'themes' ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {expandedSection === 'themes' && insights?.themes && (
          <div className="mt-4 p-4 bg-black/20 rounded-xl">
            {/* Tag cloud will be rendered here - for now show as list */}
            <div className="flex flex-wrap gap-3">
              {insights.themes.map((theme, idx) => (
                <div
                  key={idx}
                  className="px-4 py-2 bg-gradient-to-r from-[#EA580C]/20 to-[#F7931A]/20 border border-[#F7931A]/30 rounded-full text-white text-sm font-medium"
                  style={{
                    fontSize: `${Math.max(0.875, Math.min(1.25, theme.weight / 2))}rem`,
                  }}
                >
                  {theme.name}
                  <span className="ml-2 text-[#94A3B8] text-xs">({theme.source_count})</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Research Gaps Section */}
      <div className="mb-6">
        <button
          onClick={() => toggleSection('gaps')}
          className="w-full flex items-center justify-between p-4 bg-black/30 rounded-xl hover:bg-black/40 transition-all"
        >
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-[#F7931A]" />
            <h3 className="text-lg font-heading font-bold text-white">
              Research Gaps
            </h3>
          </div>
          <svg
            className={`w-5 h-5 text-[#94A3B8] transition-transform ${
              expandedSection === 'gaps' ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {expandedSection === 'gaps' && insights?.research_gaps && (
          <div className="mt-4 p-4 bg-black/20 rounded-xl">
            <ul className="space-y-3">
              {insights.research_gaps.map((gap, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2 rounded-full bg-[#F7931A] flex-shrink-0" />
                  <p className="text-[#94A3B8] leading-relaxed">{gap}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Cross-References Section */}
      <div className="mb-6">
        <button
          onClick={() => toggleSection('cross-refs')}
          className="w-full flex items-center justify-between p-4 bg-black/30 rounded-xl hover:bg-black/40 transition-all"
        >
          <div className="flex items-center gap-3">
            <Link2 className="w-5 h-5 text-[#F7931A]" />
            <h3 className="text-lg font-heading font-bold text-white">
              Cross-References
            </h3>
          </div>
          <svg
            className={`w-5 h-5 text-[#94A3B8] transition-transform ${
              expandedSection === 'cross-refs' ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {expandedSection === 'cross-refs' && insights?.cross_references && (
          <div className="mt-4 p-4 bg-black/20 rounded-xl">
            <ul className="space-y-4">
              {insights.cross_references.map((ref, idx) => (
                <li key={idx} className="border-l-2 border-[#F7931A]/50 pl-4">
                  <p className="text-white font-medium mb-2">{ref.connection}</p>
                  <div className="flex flex-wrap gap-2">
                    {ref.sources.map((source, sIdx) => (
                      <span
                        key={sIdx}
                        className="text-xs px-2 py-1 bg-[#F7931A]/20 text-[#F7931A] rounded-full"
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Suggested Searches Section */}
      <div>
        <button
          onClick={() => toggleSection('searches')}
          className="w-full flex items-center justify-between p-4 bg-black/30 rounded-xl hover:bg-black/40 transition-all"
        >
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-[#F7931A]" />
            <h3 className="text-lg font-heading font-bold text-white">
              Suggested Searches
            </h3>
          </div>
          <svg
            className={`w-5 h-5 text-[#94A3B8] transition-transform ${
              expandedSection === 'searches' ? 'rotate-180' : ''
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {expandedSection === 'searches' && insights?.suggested_searches && (
          <div className="mt-4 p-4 bg-black/20 rounded-xl">
            <ul className="space-y-2">
              {insights.suggested_searches.map((search, idx) => (
                <li
                  key={idx}
                  className="px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-[#94A3B8] hover:border-[#F7931A]/50 hover:text-white transition-all cursor-pointer"
                >
                  {search}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
