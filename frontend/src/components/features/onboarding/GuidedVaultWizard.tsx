'use client';

import React, { useState } from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import GradientButton from '@/components/ui/GradientButton';

interface GuidedVaultWizardProps {
  onComplete: () => void;
}

const GuidedVaultWizard: React.FC<GuidedVaultWizardProps> = ({ onComplete }) => {
  const { updateOnboarding } = useOnboarding();
  const [vaultName, setVaultName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleNext = async () => {
    if (!vaultName.trim()) return;

    setIsSubmitting(true);
    try {
      // Store vault name in onboarding data and advance to step 2
      await updateOnboarding({
        step: 'guided-2',
        data: { vaultName: vaultName.trim() },
      });
    } catch (error) {
      console.error('Failed to advance to step 2:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && vaultName.trim()) {
      handleNext();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center text-white font-bold text-sm">
            1
          </div>
          <div className="w-16 h-1 bg-white/10" />
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[#94A3B8] font-bold text-sm">
            2
          </div>
          <div className="w-16 h-1 bg-white/10" />
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[#94A3B8] font-bold text-sm">
            3
          </div>
        </div>
        <p className="text-center text-[#94A3B8] text-sm">Step 1 of 3</p>
      </div>

      {/* Main Content */}
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
        <h2 className="text-3xl font-bold text-white mb-2">Name Your Vault</h2>
        <p className="text-[#94A3B8] mb-8">
          Give your knowledge vault a descriptive name. You can always change this later.
        </p>

        <div className="mb-8">
          <label htmlFor="vault-name" className="block text-white font-semibold mb-3">
            Vault Name
          </label>
          <input
            id="vault-name"
            type="text"
            value={vaultName}
            onChange={(e) => setVaultName(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., AI Research Papers 2025"
            className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-[#94A3B8]/50 focus:border-[#F7931A] focus:outline-none transition-colors"
            autoFocus
          />
        </div>

        <div className="flex justify-end">
          <GradientButton
            onClick={handleNext}
            disabled={!vaultName.trim() || isSubmitting}
            isLoading={isSubmitting}
          >
            Next
          </GradientButton>
        </div>
      </div>

      {/* Helpful Tip */}
      <div className="mt-6 text-center text-[#94A3B8] text-sm">
        💡 Tip: Choose a name that describes the topic or purpose of your research
      </div>
    </div>
  );
};

export default GuidedVaultWizard;
