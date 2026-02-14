/**
 * Loading skeleton for annotation cards
 * Matches AnnotationCard dimensions and layout
 */
export function AnnotationCardSkeleton() {
  return (
    <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-4 animate-pulse">
      {/* Header with avatar and author info */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Avatar skeleton */}
          <div className="w-8 h-8 rounded-full bg-white/10" />
          <div>
            {/* Author name skeleton */}
            <div className="h-4 w-24 bg-white/10 rounded mb-1" />
            {/* Timestamp skeleton */}
            <div className="h-3 w-32 bg-white/10 rounded" />
          </div>
        </div>

        {/* Optional page number badge skeleton */}
        <div className="h-5 w-12 bg-white/10 rounded-full" />
      </div>

      {/* Annotation text skeleton */}
      <div className="space-y-2 mb-3">
        <div className="h-4 bg-white/10 rounded w-full" />
        <div className="h-4 bg-white/10 rounded w-5/6" />
        <div className="h-4 bg-white/10 rounded w-4/6" />
      </div>

      {/* Reply count indicator skeleton */}
      <div className="h-4 w-20 bg-white/10 rounded" />
    </div>
  );
}
