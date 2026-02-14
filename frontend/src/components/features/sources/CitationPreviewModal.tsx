'use client';

import { useState } from 'react';
import { Copy, FileText } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { CitationResponse } from '@/lib/api/citations';
import { toast } from '@/hooks/useToast';

interface CitationPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  citation: CitationResponse;
  format: string;
  sourceTitle: string;
}

const FORMAT_LABELS: Record<string, string> = {
  apa7: 'APA 7th Edition',
  mla9: 'MLA 9th Edition',
  chicago17: 'Chicago 17th Edition',
  bibtex: 'BibTeX',
  ieee: 'IEEE',
  harvard: 'Harvard',
};

export function CitationPreviewModal({
  isOpen,
  onClose,
  citation,
  format,
  sourceTitle,
}: CitationPreviewModalProps) {
  const [isCopying, setIsCopying] = useState(false);

  const formatLabel = FORMAT_LABELS[format] || format.toUpperCase();
  const truncatedTitle = sourceTitle.length > 50
    ? `${sourceTitle.substring(0, 50)}...`
    : sourceTitle;

  const copyToClipboard = async (text: string) => {
    setIsCopying(true);
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: `Copied ${formatLabel} citation`,
        description: `Citation for "${truncatedTitle}" copied to clipboard.`,
      });
    } catch (error) {
      // Fallback for browsers without clipboard API
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();

      try {
        document.execCommand('copy');
        toast({
          title: `Copied ${formatLabel} citation`,
          description: `Citation for "${truncatedTitle}" copied to clipboard.`,
        });
      } catch (err) {
        toast({
          title: 'Copy failed',
          description: 'Failed to copy citation to clipboard.',
        });
      } finally {
        document.body.removeChild(textarea);
      }
    } finally {
      setIsCopying(false);
    }
  };

  const handleCopyHtml = () => copyToClipboard(citation.citation_html);
  const handleCopyPlainText = () => copyToClipboard(citation.citation);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            {formatLabel}
          </DialogTitle>
        </DialogHeader>

        {/* Citation preview */}
        <div className="my-6">
          <div className="bg-black/50 border border-white/10 rounded-xl p-6">
            <div
              className="text-white/90 leading-relaxed font-mono text-sm"
              dangerouslySetInnerHTML={{ __html: citation.citation_html }}
            />
          </div>

          {/* Citation metadata */}
          <div className="mt-4 flex items-center gap-4 text-xs text-[#94A3B8]">
            <span className="inline-flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Source: {citation.source === 'ai' ? 'AI Generated' : 'Structured'}
            </span>
            {citation.cached && (
              <span className="inline-flex items-center gap-1">
                • Cached
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleCopyHtml}
            disabled={isCopying}
            className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            <Copy className="w-4 h-4" />
            Copy Citation
          </button>

          <button
            onClick={handleCopyPlainText}
            disabled={isCopying}
            className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-white/5 border border-white/20 text-white font-semibold uppercase tracking-wider rounded-full hover:bg-white/10 hover:border-[#F7931A]/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FileText className="w-4 h-4" />
            Copy as Plain Text
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
