export function VaultCardSkeleton() {
  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between gap-4 mb-3">
          {/* Title placeholder */}
          <div className="h-6 bg-white/5 rounded w-2/3"></div>
          {/* Badge placeholder */}
          <div className="h-5 bg-white/5 rounded-full w-20 shrink-0"></div>
        </div>
        {/* Description placeholder */}
        <div className="space-y-2">
          <div className="h-4 bg-white/5 rounded w-full"></div>
          <div className="h-4 bg-white/5 rounded w-3/4"></div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center gap-6 text-sm mt-6">
        {/* Source count placeholder */}
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 bg-white/5 rounded"></div>
          <div className="h-4 bg-white/5 rounded w-16"></div>
        </div>

        {/* Member count placeholder */}
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 bg-white/5 rounded"></div>
          <div className="h-4 bg-white/5 rounded w-16"></div>
        </div>

        {/* Last updated placeholder */}
        <div className="flex items-center gap-2 ml-auto">
          <div className="h-4 w-4 bg-white/5 rounded"></div>
          <div className="h-4 bg-white/5 rounded w-20"></div>
        </div>
      </div>
    </div>
  );
}
