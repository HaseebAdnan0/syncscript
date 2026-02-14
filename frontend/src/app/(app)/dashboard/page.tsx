'use client';

import { ErrorBoundary, type FallbackProps } from 'react-error-boundary';
import WelcomeHeader from '@/components/features/dashboard/WelcomeHeader';
import ContinueResearch from '@/components/features/dashboard/ContinueResearch';
import RecentActivity from '@/components/features/dashboard/RecentActivity';
import AnalyticsSection from '@/components/features/dashboard/AnalyticsSection';
import QuickActionsFAB from '@/components/features/dashboard/QuickActionsFAB';
import { AlertTriangle } from 'lucide-react';

// Error fallback component for failed sections
function SectionErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="bg-[#0F1115] border border-red-500/20 rounded-2xl p-8">
      <div className="flex items-start gap-4">
        <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
          <AlertTriangle className="h-6 w-6 text-red-500" />
        </div>
        <div className="flex-1">
          <h3 className="text-white font-bold mb-2">Failed to load section</h3>
          <p className="text-white/60 text-sm mb-4">{error.message}</p>
          <button
            onClick={resetErrorBoundary}
            className="text-sm text-[#F7931A] hover:text-[#FFD600] transition-colors uppercase tracking-wide font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#030304] p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Welcome Header */}
        <ErrorBoundary FallbackComponent={SectionErrorFallback}>
          <WelcomeHeader />
        </ErrorBoundary>

        {/* Continue Research */}
        <ErrorBoundary FallbackComponent={SectionErrorFallback}>
          <ContinueResearch />
        </ErrorBoundary>

        {/* Recent Activity */}
        <ErrorBoundary FallbackComponent={SectionErrorFallback}>
          <RecentActivity />
        </ErrorBoundary>

        {/* Analytics Section */}
        <ErrorBoundary FallbackComponent={SectionErrorFallback}>
          <AnalyticsSection />
        </ErrorBoundary>

        {/* Quick Actions FAB (fixed position) */}
        <QuickActionsFAB />
      </div>
    </div>
  );
}
