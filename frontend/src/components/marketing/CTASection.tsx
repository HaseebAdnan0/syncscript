'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight } from 'lucide-react';

export default function CTASection() {
  const [email, setEmail] = useState('');
  const router = useRouter();

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (email) {
      router.push(`/register?email=${encodeURIComponent(email)}`);
    }
  };

  return (
    <section className="py-24 bg-gradient-to-b from-[#030304] via-[#0F1115] to-[#1a0f0a]">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center">
          {/* Headline */}
          <h2 className="font-heading text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Start Your{' '}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              Research Journey
            </span>{' '}
            Today
          </h2>

          {/* Subtext */}
          <p className="text-[#94A3B8] text-lg md:text-xl mb-12 max-w-2xl mx-auto">
            Join thousands of researchers collaborating on breakthrough
            discoveries. Start free, no credit card required.
          </p>

          {/* Email Form */}
          <form
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto"
          >
            <div className="flex-1 relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-white/40 focus:border-[#F7931A] focus:outline-none transition-colors duration-300"
              />
            </div>
            <button
              type="submit"
              className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2 whitespace-nowrap"
            >
              Get Started
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>

          {/* Trust Badge */}
          <p className="text-[#94A3B8] text-sm mt-6">
            Free forever. Upgrade anytime.{' '}
            <span className="text-white/60">No credit card required.</span>
          </p>
        </div>
      </div>
    </section>
  );
}
