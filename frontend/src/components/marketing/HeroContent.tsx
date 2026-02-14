'use client';

import Link from 'next/link';

export function HeroContent() {
  return (
    <div className="flex flex-col items-start gap-8 max-w-xl">
      {/* Headlines */}
      <div className="space-y-2">
        <h1 className="font-heading text-6xl md:text-7xl font-bold text-white leading-tight">
          Collaborative Research
        </h1>
        <h1 className="font-heading text-6xl md:text-7xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent leading-tight">
          Reimagined
        </h1>
      </div>

      {/* Subheadline */}
      <p className="text-lg md:text-xl text-[#94A3B8] leading-relaxed">
        Build shared knowledge vaults, collaborate in real-time, and manage citations with AI-powered insights.
        The future of academic research is collaborative.
      </p>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
        {/* Start Free Button - Primary Gradient */}
        <Link
          href="/register"
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all text-center"
        >
          Start Free
        </Link>

        {/* Watch Demo Button - Outline Style */}
        <button
          className="border-2 border-white/20 text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 hover:border-[#F7931A] hover:bg-[#F7931A]/10 transition-all"
        >
          Watch Demo
        </button>
      </div>
    </div>
  );
}
