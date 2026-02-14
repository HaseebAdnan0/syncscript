import { HeroBackground } from '@/components/marketing/HeroBackground';
import AnimatedOrb from '@/components/marketing/AnimatedOrb';

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
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-4 font-heading">
                Collaborative Research
              </h1>
              <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-6 font-heading">
                Reimagined
              </h2>
              <p className="text-lg md:text-xl text-[#94A3B8] max-w-2xl mx-auto lg:mx-0 mb-8">
                Build Knowledge Vaults with your team. Share sources, annotate PDFs, and collaborate in real-time.
              </p>
              <div className="flex items-center justify-center lg:justify-start gap-4 flex-wrap">
                <a
                  href="/register"
                  className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
                >
                  Start Free
                </a>
                <button className="border-2 border-white/20 text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 hover:border-[#F7931A] transition-all">
                  Watch Demo
                </button>
              </div>
            </div>

            {/* Right Column - Animated Orb */}
            <div className="order-1 lg:order-2">
              <AnimatedOrb />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
