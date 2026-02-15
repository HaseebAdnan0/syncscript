'use client';

import Link from 'next/link';
import { Source } from '@/lib/types/sources';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';

interface SourceCardProps {
  source: Source;
  vaultId: string;
}

export function SourceCard({ source, vaultId }: SourceCardProps) {
  // Truncate URL or citation preview
  const previewText = source.url || (source.metadata?.citation as string) || '';
  const truncatedPreview = previewText.length > 80
    ? previewText.substring(0, 80) + '...'
    : previewText;

  return (
    <Link
      href={`/vaults/${vaultId}/sources/${source.id}`}
      className="block bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all duration-300"
    >
      {/* Header with type badge */}
      <div className="flex items-start justify-between mb-4">
        <Badge variant="default" className="capitalize">
          {source.source_type}
        </Badge>
        <span className="text-xs text-[#94A3B8]">
          {format(new Date(source.created_at), 'MMM d, yyyy')}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
        {source.title}
      </h3>

      {/* Preview text */}
      <p className="text-sm text-[#94A3B8] mb-4 line-clamp-2">
        {truncatedPreview}
      </p>

      {/* Footer with contributor */}
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center text-xs font-bold text-white">
          {source.created_by?.charAt(0).toUpperCase() || 'U'}
        </div>
        <span className="text-xs text-[#94A3B8]">
          Added by {source.created_by || 'Unknown'}
        </span>
      </div>
    </Link>
  );
}
