import { HeroBackground } from '@/components/marketing/HeroBackground';
import { HeroContent } from '@/components/marketing/HeroContent';
import AnimatedOrb from '@/components/marketing/AnimatedOrb';
import FloatingStatCard from '@/components/marketing/FloatingStatCard';
import { Database, FileText, Users } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section with Two-Column Layout */}
      <section className="min-h-screen relative">
        <HeroBackground />
        <div className="container mx-auto px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center min-h-screen py-20">
            {/* Left Column - Content */}
            <div className="text-center lg:text-left order-2 lg:order-1">
              <HeroContent />
            </div>

            {/* Right Column - Animated Orb with Floating Stat Cards */}
            <div className="order-1 lg:order-2">
              {/* Container for orb and stat cards */}
              <div className="relative flex flex-col items-center justify-center">
                {/* Stat Cards - Stack on mobile, float around orb on desktop */}
                <div className="flex flex-col md:hidden gap-4 mb-8 w-full max-w-sm">
                  <FloatingStatCard
                    icon={Database}
                    number="10K+"
                    label="Active Vaults"
                    position="top"
                    delay={0}
                  />
                  <FloatingStatCard
                    icon={FileText}
                    number="50K+"
                    label="Sources Indexed"
                    position="left"
                    delay={0.2}
                  />
                  <FloatingStatCard
                    icon={Users}
                    number="25K+"
                    label="Researchers"
                    position="right"
                    delay={0.4}
                  />
                </div>

                {/* Desktop: Orb with floating cards positioned around it */}
                <div className="relative hidden md:block">
                  <AnimatedOrb />

                  {/* Floating stat cards absolutely positioned around orb */}
                  <FloatingStatCard
                    icon={Database}
                    number="10K+"
                    label="Active Vaults"
                    position="top"
                    delay={0}
                  />
                  <FloatingStatCard
                    icon={FileText}
                    number="50K+"
                    label="Sources Indexed"
                    position="left"
                    delay={0.2}
                  />
                  <FloatingStatCard
                    icon={Users}
                    number="25K+"
                    label="Researchers"
                    position="right"
                    delay={0.4}
                  />
                </div>

                {/* Mobile: Just the orb (stat cards shown above) */}
                <div className="md:hidden">
                  <AnimatedOrb />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
