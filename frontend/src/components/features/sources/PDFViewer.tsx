'use client';

import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFViewerProps {
  url: string;
  className?: string;
}

export function PDFViewer({ url, className = '' }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setIsLoading(false);
    setError(null);
  }

  function onDocumentLoadError(error: Error) {
    console.error('PDF load error:', error);
    setError('Failed to load PDF. Please try again or check the file URL.');
    setIsLoading(false);
  }

  function goToPrevPage() {
    setPageNumber((prev) => Math.max(prev - 1, 1));
  }

  function goToNextPage() {
    setPageNumber((prev) => Math.min(prev + 1, numPages || prev));
  }

  function handlePageInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 1 && value <= (numPages || 1)) {
      setPageNumber(value);
    }
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Page Navigation Controls */}
      {numPages && (
        <div className="flex items-center justify-center gap-4 mb-4 bg-[#0F1115] border border-white/10 rounded-lg px-4 py-3">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Previous page"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>

          <div className="flex items-center gap-2">
            <span className="text-sm text-[#94A3B8]">Page</span>
            <input
              type="number"
              min={1}
              max={numPages}
              value={pageNumber}
              onChange={handlePageInputChange}
              className="w-16 px-2 py-1 text-center bg-black/50 border-b-2 border-white/20 focus:border-[#F7931A] focus:outline-none rounded"
            />
            <span className="text-sm text-[#94A3B8]">of {numPages}</span>
          </div>

          <button
            onClick={goToNextPage}
            disabled={pageNumber >= (numPages || 1)}
            className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Next page"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* PDF Document */}
      <div className="flex-1 overflow-auto bg-[#030304] rounded-lg border border-white/10">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-[#F7931A]" />
              <p className="text-sm text-[#94A3B8]">Loading PDF...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full p-8">
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 max-w-md text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {!error && (
          <div className="flex justify-center p-4">
            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={null}
              error={null}
            >
              <Page
                pageNumber={pageNumber}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-lg"
              />
            </Document>
          </div>
        )}
      </div>
    </div>
  );
}
