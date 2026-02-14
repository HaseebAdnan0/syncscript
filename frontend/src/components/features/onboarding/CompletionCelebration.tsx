'use client';

import React, { useEffect } from 'react';
import confetti from 'canvas-confetti';
import { Plus, Users, BookOpen } from 'lucide-react';
import GradientButton from '@/components/ui/GradientButton';

interface CompletionCelebrationProps {
  onComplete: () => void;
  onAddSource?: () => void;
  onInviteTeam?: () => void;
  onExploreFeatures?: () => void;
}

const CompletionCelebration: React.FC<CompletionCelebrationProps> = ({
  onComplete,
  onAddSource,
  onInviteTeam,
  onExploreFeatures,
}) => {
  useEffect(() => {
    // Trigger confetti animation on mount
    const duration = 3000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };

    function randomInRange(min: number, max: number) {
      return Math.random() * (max - min) + min;
    }

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        clearInterval(interval);
        return;
      }

      const particleCount = 50 * (timeLeft / duration);

      // Orange and gold confetti matching Bitcoin DeFi theme
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
        colors: ['#F7931A', '#FFD600', '#EA580C', '#FFFFFF'],
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
        colors: ['#F7931A', '#FFD600', '#EA580C', '#FFFFFF'],
      });
    }, 250);

    return () => clearInterval(interval);
  }, []);

  const handleActionClick = (action?: () => void) => {
    if (action) {
      action();
    }
    onComplete();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-lg">
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-12 max-w-2xl w-full mx-4 shadow-[0_0_50px_-10px_rgba(247,147,26,0.3)]">
        {/* Celebration Heading */}
        <div className="text-center mb-8">
          <h2 className="text-5xl font-bold mb-4 bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent font-heading">
            You&apos;re all set!
          </h2>
          <p className="text-xl text-[#94A3B8] font-body">
            Thank you for taking the time to learn SyncScript. You&apos;re now ready to build your Knowledge Vaults and collaborate with your team.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Add Source */}
          <button
            onClick={() => handleActionClick(onAddSource)}
            className="bg-[#0F1115] border border-white/10 rounded-xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 hover:shadow-[0_0_20px_-5px_rgba(247,147,26,0.3)] transition-all duration-300 group"
          >
            <div className="bg-gradient-to-br from-[#EA580C] to-[#F7931A] w-12 h-12 rounded-full flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform duration-300">
              <Plus className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-bold text-white mb-2 uppercase tracking-wider font-heading text-sm">
              Add Source
            </h3>
            <p className="text-xs text-[#94A3B8] font-body">
              Start building your research library
            </p>
          </button>

          {/* Invite Team */}
          <button
            onClick={() => handleActionClick(onInviteTeam)}
            className="bg-[#0F1115] border border-white/10 rounded-xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 hover:shadow-[0_0_20px_-5px_rgba(247,147,26,0.3)] transition-all duration-300 group"
          >
            <div className="bg-gradient-to-br from-[#F7931A] to-[#FFD600] w-12 h-12 rounded-full flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform duration-300">
              <Users className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-bold text-white mb-2 uppercase tracking-wider font-heading text-sm">
              Invite Team
            </h3>
            <p className="text-xs text-[#94A3B8] font-body">
              Collaborate with researchers
            </p>
          </button>

          {/* Explore Features */}
          <button
            onClick={() => handleActionClick(onExploreFeatures)}
            className="bg-[#0F1115] border border-white/10 rounded-xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 hover:shadow-[0_0_20px_-5px_rgba(247,147,26,0.3)] transition-all duration-300 group"
          >
            <div className="bg-gradient-to-br from-[#FFD600] to-[#F7931A] w-12 h-12 rounded-full flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform duration-300">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <h3 className="font-bold text-white mb-2 uppercase tracking-wider font-heading text-sm">
              Explore Features
            </h3>
            <p className="text-xs text-[#94A3B8] font-body">
              Learn more about SyncScript
            </p>
          </button>
        </div>

        {/* Get Started Button */}
        <div className="text-center">
          <GradientButton onClick={onComplete} className="w-full md:w-auto px-12">
            Get Started
          </GradientButton>
        </div>
      </div>
    </div>
  );
};

export default CompletionCelebration;
