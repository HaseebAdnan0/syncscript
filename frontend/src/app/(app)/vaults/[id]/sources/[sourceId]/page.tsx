'use client';

import React, { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useVault } from '@/hooks/useVaults';
import { useSourcesQuery } from '@/hooks/useSourcesQuery';
import { SourceTypeBadge } from '@/components/features/sources/SourceTypeBadge';

export default function SourceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vaultId = parseInt(params.id as string, 10);
  const sourceId = parseInt(params.sourceId as string, 10);

  const { data: vault, isLoading: vaultLoading } = useVault(vaultId);
  const { data: sourcesResponse, isLoading: sourcesLoading } = useSourcesQuery({ vaultId });

  // Find the specific source from the sources list
  const source = sourcesResponse?.find((s) => s.id === sourceId);

  // Extract citation as string for type safety
  const citation = source?.metadata?.citation;
  const citationText = typeof citation === 'string' ? citation : null;

  useEffect(() => {
    if (vault && source) {
      document.title = `${source.title} - Sources | SyncScript`;
    }
  }, [vault, source]);

  if (vaultLoading || sourcesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#030304]">
        <Loader2 className="w-8 h-8 animate-spin text-[#F7931A]" />
      </div>
    );
  }

  if (!vault || !source) {
    return (
      <div className="min-h-screen bg-[#030304] text-white p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Source Not Found</h1>
          <button
            onClick={() => router.push(`/vaults/${vaultId}/sources`)}
            className="text-[#F7931A] hover:underline flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Sources
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304] text-white">
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-[#94A3B8] mb-3">
            <button
              onClick={() => router.push(`/vaults/${vaultId}`)}
              className="hover:text-white transition-colors"
            >
              {vault.name}
            </button>
            <span>/</span>
            <button
              onClick={() => router.push(`/vaults/${vaultId}/sources`)}
              className="hover:text-white transition-colors"
            >
              Sources
            </button>
            <span>/</span>
            <span className="text-white">{source.title}</span>
          </div>

          {/* Source Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4 flex-1">
              <button
                onClick={() => router.push(`/vaults/${vaultId}/sources`)}
                className="mt-1 text-[#94A3B8] hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-bold font-heading">{source.title}</h1>
                  <SourceTypeBadge type={source.type} />
                </div>
                {/* Metadata */}
                <div className="flex items-center gap-4 text-sm text-[#94A3B8]">
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-[#F7931A] transition-colors truncate max-w-md"
                    >
                      {source.url}
                    </a>
                  )}
                  {citationText && (
                    <span className="font-mono text-xs">
                      {citationText}
                    </span>
                  )}
                  <span>Added by {source.contributor?.username || 'Unknown'}</span>
                  <span>
                    {new Date(source.createdAt).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        <div className="flex gap-8">
          {/* PDF Viewer (70%) */}
          <div className="flex-[7]">
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 min-h-[600px]">
              <div className="flex items-center justify-center h-full text-[#94A3B8]">
                <div className="text-center">
                  <p className="mb-2">PDF Viewer</p>
                  <p className="text-sm">PDF rendering will be implemented in US-017</p>
                </div>
              </div>
            </div>
          </div>

          {/* Annotation Sidebar (30%) */}
          <div className="flex-[3]">
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 min-h-[600px]">
              <div className="flex items-center justify-center h-full text-[#94A3B8]">
                <div className="text-center">
                  <p className="mb-2">Annotations Sidebar</p>
                  <p className="text-sm">Annotation UI will be implemented in US-021</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
