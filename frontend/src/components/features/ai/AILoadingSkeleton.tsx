interface AILoadingSkeletonProps {
  variant?: 'summary' | 'insights' | 'chat';
}

export function AILoadingSkeleton({ variant = 'summary' }: AILoadingSkeletonProps) {
  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
      {/* Header with pulsing animation */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] animate-ping opacity-75" />
          <div className="absolute inset-0 w-8 h-8 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A]" />
        </div>
        <div className="text-[#F7931A] font-heading text-lg font-semibold">
          {variant === 'summary' && 'Analyzing source...'}
          {variant === 'insights' && 'Discovering insights...'}
          {variant === 'chat' && 'Thinking...'}
        </div>
      </div>

      {/* Content skeletons based on variant */}
      {variant === 'summary' && (
        <div className="space-y-6">
          {/* Abstract skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-white/10 rounded-lg w-24 animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-full animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-11/12 animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
          </div>

          {/* Key findings skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-white/10 rounded-lg w-32 animate-pulse" />
            <div className="space-y-2">
              <div className="h-3 bg-white/5 rounded-lg w-11/12 animate-pulse" />
              <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
              <div className="h-3 bg-white/5 rounded-lg w-9/12 animate-pulse" />
            </div>
          </div>

          {/* Methodology skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-white/10 rounded-lg w-28 animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-full animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
          </div>
        </div>
      )}

      {variant === 'insights' && (
        <div className="space-y-6">
          {/* Themes skeleton */}
          <div className="space-y-3">
            <div className="h-4 bg-white/10 rounded-lg w-28 animate-pulse" />
            <div className="flex flex-wrap gap-2">
              <div className="h-8 bg-white/5 rounded-full w-24 animate-pulse" />
              <div className="h-8 bg-white/5 rounded-full w-32 animate-pulse" />
              <div className="h-8 bg-white/5 rounded-full w-28 animate-pulse" />
              <div className="h-8 bg-white/5 rounded-full w-36 animate-pulse" />
              <div className="h-8 bg-white/5 rounded-full w-20 animate-pulse" />
            </div>
          </div>

          {/* Research gaps skeleton */}
          <div className="space-y-3">
            <div className="h-4 bg-white/10 rounded-lg w-36 animate-pulse" />
            <div className="space-y-2">
              <div className="h-3 bg-white/5 rounded-lg w-11/12 animate-pulse" />
              <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
              <div className="h-3 bg-white/5 rounded-lg w-9/12 animate-pulse" />
            </div>
          </div>

          {/* Cross-references skeleton */}
          <div className="space-y-3">
            <div className="h-4 bg-white/10 rounded-lg w-40 animate-pulse" />
            <div className="space-y-2">
              <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
              <div className="h-3 bg-white/5 rounded-lg w-11/12 animate-pulse" />
            </div>
          </div>
        </div>
      )}

      {variant === 'chat' && (
        <div className="space-y-4">
          {/* Typing indicator */}
          <div className="flex gap-2 items-center">
            <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>

          {/* Response skeleton */}
          <div className="space-y-2 mt-4">
            <div className="h-3 bg-white/5 rounded-lg w-full animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-11/12 animate-pulse" />
            <div className="h-3 bg-white/5 rounded-lg w-10/12 animate-pulse" />
          </div>
        </div>
      )}

      {/* Footer indicator */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
          <div className="w-1.5 h-1.5 bg-[#F7931A] rounded-full animate-pulse" />
          <span>Processing with Claude AI</span>
        </div>
      </div>
    </div>
  );
}
