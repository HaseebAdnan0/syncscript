'use client';

import React from 'react';
import { XCircle, RefreshCw, X } from 'lucide-react';

interface UploadErrorStateProps {
  filename: string;
  error: string;
  onRetry: () => void;
  onDismiss: () => void;
}

/**
 * Upload error state component
 * Displays error message with retry and dismiss actions
 */
export function UploadErrorState({
  filename,
  error,
  onRetry,
  onDismiss,
}: UploadErrorStateProps) {
  // Truncate filename to 40 chars with ellipsis
  const truncatedFilename = filename.length > 40
    ? `${filename.substring(0, 37)}...`
    : filename;

  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 space-y-3">
      {/* Header with error icon and dismiss button */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-red-400 truncate">
              {truncatedFilename}
            </p>
            <p className="text-xs text-red-300 mt-1">
              Upload failed
            </p>
          </div>
        </div>

        {/* Dismiss button */}
        <button
          onClick={onDismiss}
          className="flex-shrink-0 text-red-400 hover:text-red-300 transition-colors"
          aria-label="Dismiss error"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Error message */}
      <div className="bg-black/30 border border-red-500/20 rounded px-3 py-2">
        <p className="text-xs text-red-300 font-mono">
          {error}
        </p>
      </div>

      {/* Retry button */}
      <button
        onClick={onRetry}
        className="w-full bg-gradient-to-r from-red-500 to-red-400 text-white font-semibold text-sm rounded-lg px-4 py-2 hover:scale-[1.02] transition-all duration-200 flex items-center justify-center gap-2 shadow-[0_0_15px_-3px_rgba(239,68,68,0.5)]"
      >
        <RefreshCw className="w-4 h-4" />
        Retry Upload
      </button>
    </div>
  );
}
