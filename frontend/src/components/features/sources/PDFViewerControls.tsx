'use client';

import React from 'react';
import { ZoomIn, ZoomOut, Download, Maximize, Minimize } from 'lucide-react';

interface PDFViewerControlsProps {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitWidth: () => void;
  onFitPage: () => void;
  onDownload: () => void;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  fitMode: 'width' | 'page' | 'custom';
}

export const PDFViewerControls: React.FC<PDFViewerControlsProps> = ({
  zoom,
  onZoomIn,
  onZoomOut,
  onFitWidth,
  onFitPage,
  onDownload,
  isFullscreen,
  onToggleFullscreen,
  fitMode,
}) => {
  return (
    <div className="fixed top-20 left-0 right-0 z-20 flex items-center justify-center">
      <div className="bg-[#0F1115] border border-white/10 backdrop-blur-lg rounded-full px-6 py-3 shadow-lg flex items-center gap-4">
        {/* Zoom Out */}
        <button
          onClick={onZoomOut}
          disabled={zoom <= 50}
          className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white/5 disabled:hover:border-white/10"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4 text-white" />
        </button>

        {/* Zoom Percentage */}
        <span className="text-sm font-medium text-white min-w-[60px] text-center">
          {Math.round(zoom)}%
        </span>

        {/* Zoom In */}
        <button
          onClick={onZoomIn}
          disabled={zoom >= 200}
          className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white/5 disabled:hover:border-white/10"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4 text-white" />
        </button>

        {/* Divider */}
        <div className="w-px h-6 bg-white/10" />

        {/* Fit to Width */}
        <button
          onClick={onFitWidth}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
            fitMode === 'width'
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_15px_-3px_rgba(234,88,12,0.5)]'
              : 'bg-white/5 border border-white/10 text-[#94A3B8] hover:text-white hover:bg-white/10 hover:border-[#F7931A]/50'
          }`}
          title="Fit to Width"
        >
          Fit Width
        </button>

        {/* Fit to Page */}
        <button
          onClick={onFitPage}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
            fitMode === 'page'
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_15px_-3px_rgba(234,88,12,0.5)]'
              : 'bg-white/5 border border-white/10 text-[#94A3B8] hover:text-white hover:bg-white/10 hover:border-[#F7931A]/50'
          }`}
          title="Fit to Page"
        >
          Fit Page
        </button>

        {/* Divider */}
        <div className="w-px h-6 bg-white/10" />

        {/* Download PDF */}
        <button
          onClick={onDownload}
          className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
          title="Download PDF"
        >
          <Download className="w-4 h-4 text-white" />
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={onToggleFullscreen}
          className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
          title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
        >
          {isFullscreen ? (
            <Minimize className="w-4 h-4 text-white" />
          ) : (
            <Maximize className="w-4 h-4 text-white" />
          )}
        </button>
      </div>
    </div>
  );
};
