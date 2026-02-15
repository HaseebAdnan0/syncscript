'use client';

import { useState } from 'react';
import { ExternalLink, Download, FileText, RefreshCw } from 'lucide-react';

interface PDFViewerProps {
  url: string;
  className?: string;
}

/**
 * PDF Viewer using native browser rendering
 * Handles cross-origin PDFs by using embed/object tags
 * which browsers handle natively without CORS issues
 */
export function PDFViewer({ url, className = '' }: PDFViewerProps) {
  const [hasError, setHasError] = useState(false);
  const [viewMode, setViewMode] = useState<'embed' | 'object'>('embed');

  const handleError = () => {
    if (viewMode === 'embed') {
      // Try object tag as fallback
      setViewMode('object');
    } else {
      setHasError(true);
    }
  };

  const retry = () => {
    setHasError(false);
    setViewMode('embed');
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 mb-4 bg-[#0F1115] border border-white/10 rounded-lg px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
          <FileText className="h-4 w-4 text-[#F7931A]" />
          <span>PDF Document</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={retry}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
            title="Reload PDF"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <a
            href={url}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Download</span>
          </a>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            <span className="hidden sm:inline">Open</span>
          </a>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 relative bg-[#f5f5f5] rounded-lg border border-white/10 overflow-hidden min-h-[500px]">
        {hasError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-[#030304] p-8">
            <div className="bg-[#0F1115] border border-white/10 rounded-xl p-6 max-w-md text-center">
              <FileText className="h-12 w-12 text-[#F7931A] mx-auto mb-4" />
              <p className="text-white mb-2 font-medium">PDF Preview Unavailable</p>
              <p className="text-sm text-[#94A3B8] mb-4">
                This PDF cannot be previewed directly. Click below to view it in a new tab.
              </p>
              <div className="flex items-center justify-center gap-3">
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
                >
                  Open PDF
                </a>
                <button
                  onClick={retry}
                  className="px-4 py-2 bg-white/10 border border-white/20 text-white font-bold uppercase tracking-wider text-sm rounded-full hover:bg-white/20 transition-all"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        ) : viewMode === 'embed' ? (
          <embed
            src={url}
            type="application/pdf"
            className="w-full h-full min-h-[600px]"
            onError={handleError}
          />
        ) : (
          <object
            data={url}
            type="application/pdf"
            className="w-full h-full min-h-[600px]"
            onError={handleError}
          >
            {/* Fallback if object tag also fails */}
            <div className="flex items-center justify-center h-full bg-[#030304]">
              <div className="text-center p-8">
                <FileText className="h-12 w-12 text-[#F7931A] mx-auto mb-4" />
                <p className="text-white mb-4">Your browser cannot display this PDF</p>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm rounded-full"
                >
                  Open PDF
                </a>
              </div>
            </div>
          </object>
        )}
      </div>
    </div>
  );
}
