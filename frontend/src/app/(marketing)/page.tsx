import { HeroSection } from '@/components/marketing/HeroSection';
import StatsTicker from '@/components/marketing/StatsTicker';
import FeatureCard from '@/components/marketing/FeatureCard';
import { Zap } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <StatsTicker />

      {/* Temporary test of FeatureCard */}
      <div className="container mx-auto px-6 py-12">
        <FeatureCard
          icon={Zap}
          title="Test Feature"
          description="This is a test to verify the FeatureCard component renders correctly with all design system elements."
        />
      </div>
    </div>
  );
}
