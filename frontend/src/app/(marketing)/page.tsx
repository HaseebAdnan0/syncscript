import { HeroSection } from '@/components/marketing/HeroSection';
import StatsTicker from '@/components/marketing/StatsTicker';
import { FeaturesSection } from '@/components/marketing/FeaturesSection';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <StatsTicker />
      <FeaturesSection />
    </div>
  );
}
