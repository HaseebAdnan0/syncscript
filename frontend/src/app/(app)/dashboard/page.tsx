'use client';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#030304] p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Placeholder content for now - will be filled by subsequent user stories */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Dashboard
          </h1>
          <p className="text-[#94A3B8]">
            Welcome to your research dashboard
          </p>
        </div>

        {/* Grid layout for future sections */}
        <div className="grid grid-cols-1 gap-6">
          {/* Welcome header section - to be added in US-007 */}
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <p className="text-white/60">Welcome header component will go here</p>
          </div>

          {/* Continue research section - to be added in US-008 */}
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <p className="text-white/60">Continue research section will go here</p>
          </div>

          {/* Recent activity and analytics - to be added in later user stories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
              <p className="text-white/60">Recent activity will go here</p>
            </div>
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
              <p className="text-white/60">Analytics will go here</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
