export function VaultDetailSkeleton() {
  return (
    <div className="min-h-screen bg-[#030304] animate-pulse">
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Back button placeholder */}
          <div className="flex items-center gap-2 mb-6">
            <div className="h-5 w-5 bg-white/5 rounded"></div>
            <div className="h-5 bg-white/5 rounded w-32"></div>
          </div>

          {/* Title and description placeholders */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="h-10 bg-white/5 rounded w-2/3"></div>
              <div className="h-6 bg-white/5 rounded w-full"></div>
              <div className="h-6 bg-white/5 rounded w-4/5"></div>
            </div>
            {/* Presence indicator placeholder */}
            <div className="flex-shrink-0">
              <div className="h-8 bg-white/5 rounded-full w-32"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content with tabs */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Tab list placeholder */}
        <div className="flex gap-8 border-b border-white/10 mb-8">
          <div className="pb-4 px-2">
            <div className="h-6 bg-white/5 rounded w-24"></div>
          </div>
          <div className="pb-4 px-2">
            <div className="h-6 bg-white/5 rounded w-24"></div>
          </div>
          <div className="pb-4 px-2">
            <div className="h-6 bg-white/5 rounded w-24"></div>
          </div>
        </div>

        {/* Tab content placeholder - card list */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-[#0F1115] border border-white/10 rounded-2xl p-6"
            >
              <div className="space-y-3">
                <div className="h-6 bg-white/5 rounded w-3/4"></div>
                <div className="h-4 bg-white/5 rounded w-full"></div>
                <div className="flex items-center gap-4 mt-4">
                  <div className="h-4 bg-white/5 rounded w-24"></div>
                  <div className="h-4 bg-white/5 rounded w-24"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
