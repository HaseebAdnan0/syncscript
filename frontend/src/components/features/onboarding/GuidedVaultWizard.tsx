'use client';

import React, { useState, useEffect } from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import GradientButton from '@/components/ui/GradientButton';

const GuidedVaultWizard: React.FC = () => {
  const { step, data, updateOnboarding } = useOnboarding();
  const [vaultName, setVaultName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [collaboratorEmail, setCollaboratorEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Determine current step number from step string
  const currentStep = step === 'guided-1' ? 1 : step === 'guided-2' ? 2 : step === 'guided-3' ? 3 : 1;

  // Load saved data from context
  useEffect(() => {
    if (data?.vaultName && typeof data.vaultName === 'string') {
      setVaultName(data.vaultName);
    }
    if (data?.sourceUrl && typeof data.sourceUrl === 'string') {
      setSourceUrl(data.sourceUrl);
    }
    if (data?.collaboratorEmail && typeof data.collaboratorEmail === 'string') {
      setCollaboratorEmail(data.collaboratorEmail);
    }
  }, [data]);

  // Basic URL validation
  const isValidUrl = (url: string): boolean => {
    if (!url.trim()) return true; // Allow empty (optional)
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  // Basic email validation
  const isValidEmail = (email: string): boolean => {
    if (!email.trim()) return true; // Allow empty (optional)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleStep1Next = async () => {
    if (!vaultName.trim()) return;

    setIsSubmitting(true);
    try {
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

  const handleStep2Next = async () => {
    // Validate URL if provided
    if (sourceUrl.trim() && !isValidUrl(sourceUrl)) {
      setUrlError('Please enter a valid URL');
      return;
    }

    setIsSubmitting(true);
    setUrlError(null);
    try {
      await updateOnboarding({
        step: 'guided-3',
        data: {
          vaultName: data?.vaultName || vaultName,
          sourceUrl: sourceUrl.trim()
        },
      });
    } catch (error) {
      console.error('Failed to advance to step 3:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStep2Back = async () => {
    setIsSubmitting(true);
    try {
      await updateOnboarding({
        step: 'guided-1',
        data: {
          vaultName: data?.vaultName || vaultName,
          sourceUrl: sourceUrl
        },
      });
    } catch (error) {
      console.error('Failed to go back to step 1:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStep2Skip = async () => {
    setIsSubmitting(true);
    try {
      await updateOnboarding({
        step: 'guided-3',
        data: {
          vaultName: data?.vaultName || vaultName,
          sourceUrl: ''
        },
      });
    } catch (error) {
      console.error('Failed to skip to step 3:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStep3Back = async () => {
    setIsSubmitting(true);
    try {
      await updateOnboarding({
        step: 'guided-2',
        data: {
          vaultName: data?.vaultName || vaultName,
          sourceUrl: data?.sourceUrl || sourceUrl,
          collaboratorEmail: collaboratorEmail
        },
      });
    } catch (error) {
      console.error('Failed to go back to step 2:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStep3Skip = async () => {
    // Skip proceeds to creation without collaborator
    handleCreateVault('');
  };

  const handleCreateVault = async (email?: string) => {
    // Validate email if provided
    const emailToUse = email !== undefined ? email : collaboratorEmail;
    if (emailToUse.trim() && !isValidEmail(emailToUse)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    setIsSubmitting(true);
    setEmailError(null);
    try {
      await updateOnboarding({
        step: 'tutorial',
        data: {
          vaultName: data?.vaultName || vaultName,
          sourceUrl: data?.sourceUrl || sourceUrl,
          collaboratorEmail: emailToUse.trim()
        },
      });
    } catch (error) {
      console.error('Failed to complete wizard:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (currentStep === 1 && vaultName.trim()) {
        handleStep1Next();
      } else if (currentStep === 2) {
        handleStep2Next();
      } else if (currentStep === 3) {
        handleCreateVault();
      }
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
            currentStep >= 1
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
              : 'bg-white/10 text-[#94A3B8]'
          }`}>
            1
          </div>
          <div className={`w-16 h-1 ${currentStep >= 2 ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]' : 'bg-white/10'}`} />
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
            currentStep >= 2
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
              : 'bg-white/10 text-[#94A3B8]'
          }`}>
            2
          </div>
          <div className={`w-16 h-1 ${currentStep >= 3 ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]' : 'bg-white/10'}`} />
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
            currentStep >= 3
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
              : 'bg-white/10 text-[#94A3B8]'
          }`}>
            3
          </div>
        </div>
        <p className="text-center text-[#94A3B8] text-sm">Step {currentStep} of 3</p>
      </div>

      {/* Step 1: Name Vault */}
      {currentStep === 1 && (
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
              onClick={handleStep1Next}
              disabled={!vaultName.trim() || isSubmitting}
              isLoading={isSubmitting}
            >
              Next
            </GradientButton>
          </div>

          {/* Helpful Tip */}
          <div className="mt-6 text-center text-[#94A3B8] text-sm">
            💡 Tip: Choose a name that describes the topic or purpose of your research
          </div>
        </div>
      )}

      {/* Step 2: Add Source */}
      {currentStep === 2 && (
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
          <h2 className="text-3xl font-bold text-white mb-2">Add Your First Source</h2>
          <p className="text-[#94A3B8] mb-8">
            Start building your knowledge vault by adding a research paper, article, or any URL you want to save.
          </p>

          <div className="mb-8">
            <label htmlFor="source-url" className="block text-white font-semibold mb-3">
              Source URL (Optional)
            </label>
            <input
              id="source-url"
              type="url"
              value={sourceUrl}
              onChange={(e) => {
                setSourceUrl(e.target.value);
                setUrlError(null);
              }}
              onKeyDown={handleKeyDown}
              placeholder="https://arxiv.org/abs/..."
              className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-[#94A3B8]/50 focus:border-[#F7931A] focus:outline-none transition-colors"
              autoFocus
            />
            {urlError && (
              <p className="mt-2 text-sm text-red-400">{urlError}</p>
            )}
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={handleStep2Back}
              disabled={isSubmitting}
              className="text-[#94A3B8] hover:text-white transition-colors px-4 py-2"
            >
              Back
            </button>
            <div className="flex gap-4 items-center">
              <button
                onClick={handleStep2Skip}
                disabled={isSubmitting}
                className="text-[#94A3B8] hover:text-white transition-colors text-sm underline"
              >
                Skip this step
              </button>
              <GradientButton
                onClick={handleStep2Next}
                disabled={isSubmitting}
                isLoading={isSubmitting}
              >
                Next
              </GradientButton>
            </div>
          </div>

          {/* Helpful Tip */}
          <div className="mt-6 text-center text-[#94A3B8] text-sm">
            💡 Tip: You can add sources from arXiv, PDFs, web articles, or any research material
          </div>
        </div>
      )}
    </div>
  );
};

export default GuidedVaultWizard;
