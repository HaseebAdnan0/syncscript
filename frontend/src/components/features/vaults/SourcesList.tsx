'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FileText, Calendar, User } from 'lucide-react';
import { useSources } from '@/hooks/useSources';
import { SourceTypeBadge } from '../sources/SourceTypeBadge';
import { AddSourceModal } from '../sources/AddSourceModal';
import EmptySourcesState from './EmptySourcesState';
import type { Source } from '@/lib/types/sources';
import type { VaultRole } from '@/lib/types/vault';

interface SourcesListProps {
  vaultId: string;
  userRole: VaultRole;
}

export function SourcesList({ vaultId, userRole }: SourcesListProps) {
  const { data: sources = [], isLoading, error } = useSources(vaultId);
  const [isAddSourceModalOpen, setIsAddSourceModalOpen] = useState(false);

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse"
          >
            <div className="h-6 bg-white/5 rounded w-3/4 mb-3" />
            <div className="h-4 bg-white/5 rounded w-1/2 mb-4" />
            <div className="flex gap-4">
              <div className="h-4 bg-white/5 rounded w-24" />
              <div className="h-4 bg-white/5 rounded w-24" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6">
        <p className="text-red-400">Failed to load sources. Please try again.</p>
      </div>
    );
  }

  // Empty state
  if (sources.length === 0) {
    const canAddSource = userRole === 'OWNER' || userRole === 'CONTRIBUTOR';
    return (
      <>
        <EmptySourcesState
          onAddSource={() => setIsAddSourceModalOpen(true)}
          canAddSource={canAddSource}
        />
        <AddSourceModal
          open={isAddSourceModalOpen}
          onOpenChange={setIsAddSourceModalOpen}
          vaultId={vaultId}
        />
      </>
    );
  }

  return (
    <>
      <div className="space-y-4">
        {sources.map((source) => (
          <SourceCard key={source.id} source={source} vaultId={vaultId} />
        ))}
      </div>
      <AddSourceModal
        open={isAddSourceModalOpen}
        onOpenChange={setIsAddSourceModalOpen}
        vaultId={vaultId}
      />
    </>
  );
}

interface SourceCardProps {
  source: Source;
  vaultId: string;
}

function SourceCard({ source, vaultId }: SourceCardProps) {
  const formattedDate = formatDate(source.created_at);
  const truncatedUrl = truncateUrl(source.url, 60);

  return (
    <Link
      href={`/vaults/${vaultId}/sources/${source.id}`}
      className="block bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all duration-300"
    >
      {/* Header with title and type badge */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <FileText className="w-5 h-5 text-[#F7931A] flex-shrink-0 mt-0.5" />
          <h3 className="text-lg font-semibold text-white truncate">{source.title}</h3>
        </div>
        <SourceTypeBadge type={source.source_type} />
      </div>

      {/* URL */}
      <div className="mb-4">
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors inline-flex items-center gap-1 break-all"
        >
          {truncatedUrl}
        </a>
      </div>

      {/* Metadata: Date added and contributor */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-[#94A3B8]">
        {/* Date added */}
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4" />
          <span>Added {formattedDate}</span>
        </div>

        {/* Contributor */}
        <div className="flex items-center gap-1.5">
          <User className="w-4 h-4" />
          <span>by {source.created_by}</span>
        </div>
      </div>
    </Link>
  );
}

// Helper function to format date
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;

  // For older dates, show the full date
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// Helper function to truncate long URLs
function truncateUrl(url: string, maxLength: number): string {
  if (url.length <= maxLength) return url;
  return url.substring(0, maxLength - 3) + '...';
}
