import { HeroSection } from '@/components/marketing/HeroSection';
import StatsTicker from '@/components/marketing/StatsTicker';
import { FeaturesSection } from '@/components/marketing/FeaturesSection';
import HowItWorksSection from '@/components/marketing/HowItWorksSection';
import TestimonialsSection from '@/components/marketing/TestimonialsSection';
import PricingSection from '@/components/marketing/PricingSection';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <StatsTicker />
      <FeaturesSection />
      <HowItWorksSection />
      <TestimonialsSection />
      <PricingSection />
    </div>
  );
}
