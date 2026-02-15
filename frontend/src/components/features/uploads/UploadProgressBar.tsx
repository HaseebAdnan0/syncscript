'use client';


import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface UploadProgressBarProps {
  filename: string;
  progress: number; // 0-100
  status: 'uploading' | 'processing' | 'complete' | 'error';
}

export function UploadProgressBar({ filename, progress, status }: UploadProgressBarProps) {
  // Truncate filename to 30 chars with ellipsis
  const truncatedFilename = filename.length > 30
    ? `${filename.substring(0, 27)}...`
    : filename;

  // Status colors
  const statusColors = {
    uploading: 'from-[#EA580C] to-[#F7931A]', // Orange gradient
    processing: 'from-blue-500 to-blue-400',   // Blue gradient
    complete: 'from-green-500 to-green-400',   // Green gradient
    error: 'from-red-500 to-red-400',          // Red gradient
  };

  const textColors = {
    uploading: 'text-[#F7931A]',
    processing: 'text-blue-400',
    complete: 'text-green-400',
    error: 'text-red-400',
  };

  const bgColors = {
    uploading: 'bg-[#F7931A]/10',
    processing: 'bg-blue-500/10',
    complete: 'bg-green-500/10',
    error: 'bg-red-500/10',
  };

  // Status icon
  const StatusIcon = () => {
    if (status === 'complete') {
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    }
    if (status === 'error') {
      return <XCircle className="w-5 h-5 text-red-400" />;
    }
    if (status === 'processing') {
      return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
    }
    return <Loader2 className="w-5 h-5 text-[#F7931A] animate-spin" />;
  };

  return (
    <div className={`${bgColors[status]} border border-white/10 rounded-lg p-4 transition-all`}>
      {/* Header: Filename and Icon */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-white truncate flex-1 mr-2">
          {truncatedFilename}
        </span>
        <StatusIcon />
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-black/50 rounded-full overflow-hidden mb-2">
        <div
          className={`h-full bg-gradient-to-r ${statusColors[status]} transition-all duration-300 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {/* Status Text and Percentage */}
      <div className="flex items-center justify-between text-xs">
        <span className={`${textColors[status]} font-medium`}>
          {status === 'uploading' && 'Uploading...'}
          {status === 'processing' && 'Processing...'}
          {status === 'complete' && 'Upload complete'}
          {status === 'error' && 'Upload failed'}
        </span>
        <span className="text-muted">
          {status !== 'error' ? `${Math.round(progress)}%` : ''}
        </span>
      </div>
    </div>
  );
}
