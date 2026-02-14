'use client';

import { useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { HeroSection } from '@/components/marketing/HeroSection';
import StatsTicker from '@/components/marketing/StatsTicker';
import { useAuthStore } from '@/stores/authStore';

// Lazy load below-fold sections for better performance
const FeaturesSection = dynamic(() => import('@/components/marketing/FeaturesSection').then(mod => ({ default: mod.FeaturesSection })), {
  loading: () => <SectionSkeleton />,
});
const HowItWorksSection = dynamic(() => import('@/components/marketing/HowItWorksSection'), {
  loading: () => <SectionSkeleton />,
});
const TestimonialsSection = dynamic(() => import('@/components/marketing/TestimonialsSection'), {
  loading: () => <SectionSkeleton />,
});
const PricingSection = dynamic(() => import('@/components/marketing/PricingSection'), {
  loading: () => <SectionSkeleton />,
});
const CTASection = dynamic(() => import('@/components/marketing/CTASection'), {
  loading: () => <SectionSkeleton />,
});

// Skeleton fallback for lazy-loaded sections
function SectionSkeleton() {
  return (
    <div className="py-24 bg-[#030304]">
      <div className="container mx-auto max-w-7xl px-6">
        <div className="animate-pulse space-y-8">
          {/* Skeleton heading */}
          <div className="h-12 bg-white/5 rounded-lg max-w-md mx-auto" />
          {/* Skeleton content grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-64 bg-white/5 rounded-2xl" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();

  // Redirect logged-in users to dashboard
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#030304]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/20 border-t-[#F7931A]" />
          <p className="text-sm text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render marketing page if user is logged in (redirecting)
  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen scroll-smooth">
      {/* Above-fold content loads immediately */}
      <HeroSection />
      <StatsTicker />

      {/* Below-fold sections lazy load with Suspense boundaries */}
      <Suspense fallback={<SectionSkeleton />}>
        <FeaturesSection />
      </Suspense>

      <Suspense fallback={<SectionSkeleton />}>
        <HowItWorksSection />
      </Suspense>

      <Suspense fallback={<SectionSkeleton />}>
        <TestimonialsSection />
      </Suspense>

      <Suspense fallback={<SectionSkeleton />}>
        <PricingSection />
      </Suspense>

      <Suspense fallback={<SectionSkeleton />}>
        <CTASection />
      </Suspense>
    </div>
  );
}
