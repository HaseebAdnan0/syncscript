'use client';

import { Source } from '@/lib/types/sources';
import { SourceCard } from './SourceCard';
import { SourceTableRow } from './SourceTableRow';
import { FileQuestion } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SourcesListProps {
  sources: Source[];
  vaultId: string;
  viewMode: 'grid' | 'table';
  isLoading?: boolean;
  onAddSource?: () => void;
  onEdit?: (source: Source) => void;
  onDelete?: (source: Source) => void;
}

// Loading skeleton for grid view
function SourceCardSkeleton() {
  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="h-6 w-16 bg-white/10 rounded" />
        <div className="h-4 w-20 bg-white/10 rounded" />
      </div>
      <div className="h-6 bg-white/10 rounded mb-2" />
      <div className="h-4 bg-white/10 rounded mb-4 w-3/4" />
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-white/10" />
        <div className="h-4 w-24 bg-white/10 rounded" />
      </div>
    </div>
  );
}

// Loading skeleton for table view
function SourceTableRowSkeleton() {
  return (
    <tr className="border-b border-white/5">
      <td className="px-4 py-3">
        <div className="h-6 w-16 bg-white/10 rounded animate-pulse" />
      </td>
      <td className="px-4 py-3">
        <div className="h-5 w-48 bg-white/10 rounded animate-pulse" />
      </td>
      <td className="px-4 py-3">
        <div className="h-4 w-24 bg-white/10 rounded animate-pulse" />
      </td>
      <td className="px-4 py-3">
        <div className="h-4 w-20 bg-white/10 rounded animate-pulse" />
      </td>
      <td className="px-4 py-3">
        <div className="h-4 w-4 bg-white/10 rounded animate-pulse" />
      </td>
    </tr>
  );
}

// Empty state component
function EmptyState({ onAddSource }: { onAddSource?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4">
      <div className="w-24 h-24 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center mb-6 opacity-20">
        <FileQuestion className="w-12 h-12 text-white" />
      </div>
      <h3 className="text-2xl font-bold text-white mb-2">No sources yet</h3>
      <p className="text-[#94A3B8] mb-6 text-center max-w-md">
        Start building your research vault by adding your first source. Import URLs, upload PDFs, or add citations.
      </p>
      {onAddSource && (
        <Button
          onClick={onAddSource}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
        >
          Add Your First Source
        </Button>
      )}
    </div>
  );
}

export function SourcesList({
  sources,
  vaultId,
  viewMode,
  isLoading = false,
  onAddSource,
  onEdit,
  onDelete,
}: SourcesListProps) {
  // Show loading state
  if (isLoading) {
    if (viewMode === 'grid') {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <SourceCardSkeleton key={i} />
          ))}
        </div>
      );
    } else {
      return (
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-black/50 border-b border-white/10 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Type</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Title</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Contributor</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Date Added</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {[...Array(10)].map((_, i) => (
                <SourceTableRowSkeleton key={i} />
              ))}
            </tbody>
          </table>
        </div>
      );
    }
  }

  // Show empty state
  if (!sources || sources.length === 0) {
    return <EmptyState onAddSource={onAddSource} />;
  }

  // Grid view
  if (viewMode === 'grid') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sources.map((source) => (
          <SourceCard key={source.id} source={source} vaultId={vaultId} />
        ))}
      </div>
    );
  }

  // Table view
  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-black/50 border-b border-white/10 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Type</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Title</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Contributor</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Date Added</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-[#94A3B8]">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <SourceTableRow
                key={source.id}
                source={source}
                vaultId={vaultId}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
