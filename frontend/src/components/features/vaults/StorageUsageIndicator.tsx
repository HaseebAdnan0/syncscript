'use client';



interface StorageUsageIndicatorProps {
  usedBytes: number;
  limitBytes: number;
  warning?: boolean;
}

/**
 * Storage usage indicator for vault settings
 * Shows progress bar and formatted storage text
 */
export function StorageUsageIndicator({
  usedBytes,
  limitBytes,
  warning = false,
}: StorageUsageIndicatorProps) {
  // Calculate percentage used
  const percentage = limitBytes > 0 ? (usedBytes / limitBytes) * 100 : 0;
  const clampedPercentage = Math.min(100, Math.max(0, percentage));

  // Format bytes to GB with 2 decimal places
  const formatGB = (bytes: number): string => {
    const gb = bytes / (1024 * 1024 * 1024);
    return gb.toFixed(2);
  };

  // Determine color based on usage percentage and warning state
  const getProgressColor = () => {
    if (percentage >= 95) {
      return 'bg-gradient-to-r from-red-500 to-red-400'; // Red when >95%
    } else if (warning || percentage >= 80) {
      return 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'; // Bitcoin orange when warning
    } else {
      return 'bg-gradient-to-r from-blue-500 to-blue-400'; // Blue when healthy
    }
  };

  const getTextColor = () => {
    if (percentage >= 95) {
      return 'text-red-400';
    } else if (warning || percentage >= 80) {
      return 'text-[#F7931A]'; // Bitcoin orange
    } else {
      return 'text-white/70';
    }
  };

  return (
    <div className="space-y-3">
      {/* Storage text */}
      <div className="flex items-center justify-between">
        <span className={`text-sm font-medium ${getTextColor()}`}>
          {formatGB(usedBytes)} GB / {formatGB(limitBytes)} GB used
        </span>
        <span className={`text-sm font-mono ${getTextColor()}`}>
          {clampedPercentage.toFixed(1)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-black/50 rounded-full overflow-hidden border border-white/10">
        <div
          className={`h-full transition-all duration-300 ${getProgressColor()}`}
          style={{ width: `${clampedPercentage}%` }}
        />
      </div>

      {/* Warning message when approaching limit */}
      {warning && percentage < 95 && (
        <p className="text-xs text-[#F7931A] flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          Storage approaching limit. Consider archiving old files.
        </p>
      )}

      {/* Critical warning when exceeded 95% */}
      {percentage >= 95 && (
        <p className="text-xs text-red-400 flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Storage nearly full. Delete files to upload more.
        </p>
      )}
    </div>
  );
}
