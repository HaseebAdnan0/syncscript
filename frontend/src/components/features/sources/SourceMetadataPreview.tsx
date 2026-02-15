'use client';

import { useState } from 'react';
import { Globe } from 'lucide-react';
import { SourceTypeBadge } from './SourceTypeBadge';
import type { SourceType } from '@/lib/types/sources';

interface SourceMetadataPreviewProps {
  metadata: {
    title: string;
    description?: string;
    favicon?: string;
    detectedType: SourceType;
  };
  onAddSource: (title: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function SourceMetadataPreview({
  metadata,
  onAddSource,
  onCancel,
  isLoading = false,
  error = null,
  onRetry
}: SourceMetadataPreviewProps) {
  const [editableTitle, setEditableTitle] = useState(metadata.title);

  const handleAddSource = () => {
    onAddSource(editableTitle);
  };

  // Error state
  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
        <div className="flex gap-3 justify-end">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-[#0F1115] border border-white/20 rounded-lg text-white hover:border-white/40 transition-colors"
            >
              Retry
            </button>
          )}
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-[#0F1115] border border-white/20 rounded-lg text-white hover:border-white/40 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Preview Card */}
      <div className="bg-[#0F1115] border border-white/10 rounded-xl p-6 space-y-4">
        {/* Favicon and Type Badge */}
        <div className="flex items-center gap-3">
          {metadata.favicon ? (
            <img
              src={metadata.favicon}
              alt="Site favicon"
              className="w-8 h-8 rounded"
            />
          ) : (
            <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center">
              <Globe className="w-4 h-4 text-[#94A3B8]" />
            </div>
          )}
          <SourceTypeBadge type={metadata.detectedType} />
        </div>

        {/* Editable Title */}
        <div>
          <label className="text-sm text-[#94A3B8] mb-2 block">Title</label>
          <input
            type="text"
            value={editableTitle}
            onChange={(e) => setEditableTitle(e.target.value)}
            className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors"
          />
        </div>

        {/* Description */}
        {metadata.description && (
          <div>
            <label className="text-sm text-[#94A3B8] mb-2 block">Description</label>
            <p className="text-white/80 text-sm leading-relaxed">
              {metadata.description}
            </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={onCancel}
          className="px-6 py-3 bg-[#0F1115] border border-white/20 rounded-lg text-white hover:border-white/40 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleAddSource}
          disabled={isLoading || !editableTitle.trim()}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? 'Adding...' : 'Add Source'}
        </button>
      </div>
    </div>
  );
}
