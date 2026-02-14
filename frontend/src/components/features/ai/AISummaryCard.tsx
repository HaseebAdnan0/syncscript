'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Sparkles, RefreshCw, AlertTriangle } from 'lucide-react';

interface AISummary {
  abstract: string;
  key_findings: string[];
  methodology: string;
  limitations: string;
  keywords: string[];
  language?: string;
  quality_flags?: string[];
  generated_at: string;
}

interface AISummaryCardProps {
  summary: AISummary | null;
  onRegenerate: () => void;
}

const QUALITY_FLAG_LABELS: Record<string, string> = {
  preprint: 'Preprint',
  not_peer_reviewed: 'Not Peer Reviewed',
  retracted: 'Retracted',
  non_english: 'Non-English Source',
};

export default function AISummaryCard({ summary, onRegenerate }: AISummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!summary) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="w-6 h-6 text-[#F7931A]" />
          <h3 className="text-xl font-heading font-bold text-white">AI Summary</h3>
        </div>
        <p className="text-[#94A3B8] mb-6">
          Generate an AI-powered academic summary to quickly understand this source's key findings, methodology, and limitations.
        </p>
        <button
          onClick={onRegenerate}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
        >
          Generate Summary
        </button>
      </div>
    );
  }

  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:border-[#F7931A]/50 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Sparkles className="w-6 h-6 text-[#F7931A]" />
          <h3 className="text-xl font-heading font-bold text-white">AI Summary</h3>
          {summary.language && summary.language !== 'English' && (
            <span className="text-xs bg-[#FFD600]/20 text-[#FFD600] px-2 py-1 rounded-full">
              {summary.language}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRegenerate}
            className="text-[#94A3B8] hover:text-[#F7931A] transition-colors p-2"
            title="Regenerate summary"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[#94A3B8] hover:text-white transition-colors p-2"
          >
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Quality Flags */}
      {summary.quality_flags && summary.quality_flags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {summary.quality_flags.map((flag) => (
            <div
              key={flag}
              className="flex items-center gap-1 text-xs bg-orange-500/20 text-orange-400 px-2 py-1 rounded-full border border-orange-500/30"
            >
              <AlertTriangle className="w-3 h-3" />
              {QUALITY_FLAG_LABELS[flag] || flag}
            </div>
          ))}
        </div>
      )}

      {/* Abstract (always visible) */}
      <div className="mb-6">
        <h4 className="text-sm font-bold text-[#FFD600] uppercase tracking-wider mb-2">Abstract</h4>
        <p className="text-white/90 leading-relaxed">{summary.abstract}</p>
      </div>

      {/* Expanded sections */}
      {isExpanded && (
        <div className="space-y-6 border-t border-white/10 pt-6">
          {/* Key Findings */}
          {summary.key_findings && summary.key_findings.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-[#FFD600] uppercase tracking-wider mb-3">
                Key Findings
              </h4>
              <ul className="space-y-2">
                {summary.key_findings.map((finding, idx) => (
                  <li key={idx} className="flex gap-3">
                    <span className="text-[#F7931A] mt-1">•</span>
                    <span className="text-white/90">{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Methodology */}
          {summary.methodology && (
            <div>
              <h4 className="text-sm font-bold text-[#FFD600] uppercase tracking-wider mb-2">
                Methodology
              </h4>
              <p className="text-white/90 leading-relaxed">{summary.methodology}</p>
            </div>
          )}

          {/* Limitations */}
          {summary.limitations && (
            <div>
              <h4 className="text-sm font-bold text-[#FFD600] uppercase tracking-wider mb-2">
                Limitations
              </h4>
              <p className="text-white/90 leading-relaxed">{summary.limitations}</p>
            </div>
          )}

          {/* Keywords */}
          {summary.keywords && summary.keywords.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-[#FFD600] uppercase tracking-wider mb-3">
                Keywords
              </h4>
              <div className="flex flex-wrap gap-2">
                {summary.keywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-[#F7931A]/20 text-[#F7931A] px-3 py-1 rounded-full border border-[#F7931A]/30"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Generated timestamp */}
          <div className="text-xs text-[#94A3B8] pt-2 border-t border-white/5">
            Generated {new Date(summary.generated_at).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}
