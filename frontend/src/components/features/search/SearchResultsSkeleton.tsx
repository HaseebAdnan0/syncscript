export default function SearchResultsSkeleton() {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: 5 }).map((_, index) => (
        <div
          key={index}
          className="flex items-start gap-3 p-4 rounded-lg bg-[#0F1115] border border-white/10 animate-pulse"
        >
          {/* Icon skeleton */}
          <div className="w-5 h-5 bg-white/10 rounded flex-shrink-0" />

          {/* Content skeleton */}
          <div className="flex-1 min-w-0 space-y-2">
            {/* Title skeleton */}
            <div className="h-5 bg-white/10 rounded w-3/4" />

            {/* Breadcrumb skeleton */}
            <div className="h-3 bg-white/10 rounded w-1/2" />

            {/* Snippet skeleton (2 lines) */}
            <div className="space-y-1">
              <div className="h-3 bg-white/10 rounded w-full" />
              <div className="h-3 bg-white/10 rounded w-5/6" />
            </div>
          </div>

          {/* Relevance score skeleton */}
          <div className="w-10 h-5 bg-white/10 rounded flex-shrink-0" />
        </div>
      ))}
    </div>
  );
}
