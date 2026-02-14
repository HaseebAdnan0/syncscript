'use client';

import React from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import { Compass, Sparkles, SkipForward } from 'lucide-react';

interface PathSelectionProps {
  onPathSelected: (path: 'guided' | 'demo' | 'skipped') => void;
}

const PathSelection: React.FC<PathSelectionProps> = ({ onPathSelected }) => {
  const { updateOnboarding } = useOnboarding();

  const handleSelectPath = async (path: 'guided' | 'demo' | 'skipped') => {
    try {
      // Update onboarding state with selected path
      await updateOnboarding({
        path,
        step: path === 'skipped' ? 'complete' : path === 'demo' ? 'demo' : 'guided-1',
        completed: path === 'skipped',
      });

      // Notify parent component
      onPathSelected(path);
    } catch (error) {
      console.error('Failed to select onboarding path:', error);
    }
  };

  const pathOptions = [
    {
      id: 'guided' as const,
      title: 'Create Your First Vault',
      description: 'Follow a step-by-step guide to set up your first knowledge vault',
      icon: Sparkles,
      iconBg: 'from-[#EA580C] to-[#F7931A]',
    },
    {
      id: 'demo' as const,
      title: 'Explore Demo Vault',
      description: 'Dive into a pre-populated vault with real research papers and annotations',
      icon: Compass,
      iconBg: 'from-[#F7931A] to-[#FFD600]',
    },
    {
      id: 'skipped' as const,
      title: 'Skip Tutorial',
      description: "I'm ready to explore on my own without guidance",
      icon: SkipForward,
      iconBg: 'from-[#94A3B8] to-[#64748B]',
    },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6">
      <div className="text-center mb-8 md:mb-12">
        <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-white mb-3 md:mb-4">
          Choose Your Path
        </h2>
        <p className="text-[#94A3B8] text-base md:text-lg">
          How would you like to get started with SyncScript?
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {pathOptions.map((option) => {
          const IconComponent = option.icon;
          return (
            <button
              key={option.id}
              onClick={() => handleSelectPath(option.id)}
              className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 md:p-8 text-left hover:-translate-y-2 hover:border-[#F7931A]/50 hover:shadow-[0_0_30px_-10px_rgba(247,147,26,0.5)] transition-all duration-300 group min-h-[200px] active:scale-95"
            >
              <div
                className={`w-16 h-16 rounded-full bg-gradient-to-r ${option.iconBg} flex items-center justify-center mb-6 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] group-hover:scale-110 transition-transform duration-300`}
              >
                <IconComponent className="w-8 h-8 text-white" />
              </div>

              <h3 className="text-xl md:text-2xl font-bold text-white mb-3 group-hover:text-[#F7931A] transition-colors">
                {option.title}
              </h3>

              <p className="text-sm md:text-base text-[#94A3B8] leading-relaxed">
                {option.description}
              </p>

              <div className="mt-6 flex items-center text-[#F7931A] opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span className="font-semibold uppercase tracking-wider text-sm">
                  Get Started
                </span>
                <svg
                  className="w-4 h-4 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default PathSelection;
