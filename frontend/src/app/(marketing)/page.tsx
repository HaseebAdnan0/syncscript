import { HeroSection } from '@/components/marketing/HeroSection';
import StatsTicker from '@/components/marketing/StatsTicker';
import { FeaturesSection } from '@/components/marketing/FeaturesSection';
import HowItWorksSection from '@/components/marketing/HowItWorksSection';
import TestimonialsSection from '@/components/marketing/TestimonialsSection';
import PricingCard from '@/components/marketing/PricingCard';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <StatsTicker />
      <FeaturesSection />
      <HowItWorksSection />
      <TestimonialsSection />

      {/* Temporary test section for PricingCard */}
      <section className="py-24 bg-[#030304]">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <PricingCard
              tier="Free"
              price={0}
              features={[
                { name: '1 Knowledge Vault', included: true },
                { name: 'Up to 50 sources', included: true },
                { name: 'Basic annotations', included: true },
                { name: 'Community support', included: true },
                { name: 'Real-time collaboration', included: false },
                { name: 'AI insights', included: false },
              ]}
              ctaLink="/register?plan=free"
            />
            <PricingCard
              tier="Pro"
              price={12}
              features={[
                { name: '5 Knowledge Vaults', included: true },
                { name: 'Unlimited sources', included: true },
                { name: 'Advanced annotations', included: true },
                { name: 'Priority support', included: true },
                { name: 'Real-time collaboration', included: true },
                { name: 'AI insights', included: true },
              ]}
              isPopular={true}
              ctaLink="/register?plan=pro"
            />
            <PricingCard
              tier="Team"
              price={29}
              features={[
                { name: 'Unlimited vaults', included: true },
                { name: 'Unlimited sources', included: true },
                { name: 'Team permissions', included: true },
                { name: '24/7 support', included: true },
                { name: 'Real-time collaboration', included: true },
                { name: 'Advanced AI insights', included: true },
              ]}
              ctaLink="/register?plan=team"
            />
          </div>
        </div>
      </section>
    </div>
  );
}
