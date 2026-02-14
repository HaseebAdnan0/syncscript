'use client';

import React, { useState, useEffect } from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import GradientButton from '@/components/ui/GradientButton';
import { createVault } from '@/lib/api/vaults';
import { createSource } from '@/lib/api/sources';
import { inviteVaultMember } from '@/lib/api/vaults';
import { SourceType } from '@/lib/types/sources';
import { VaultRole } from '@/lib/types/vault';

const GuidedVaultWizard: React.FC = () => {
  const { step, data, updateOnboarding } = useOnboarding();
  const [vaultName, setVaultName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [collaboratorEmail, setCollaboratorEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [creationError, setCreationError] = useState<string | null>(null);

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
    setCreationError(null);

    try {
      const finalVaultName = (data?.vaultName as string) || vaultName;
      const finalSourceUrl = (data?.sourceUrl as string) || sourceUrl;
      const finalCollaboratorEmail = emailToUse.trim();

      // Step 1: Create the vault
      const vault = await createVault({
        name: finalVaultName,
        description: `Created via guided onboarding`,
      });

      // Step 2: Add source if URL was provided
      if (finalSourceUrl) {
        try {
          await createSource({
            vault: vault.id,
            type: SourceType.URL,
            url: finalSourceUrl,
            title: finalSourceUrl, // Will be updated by backend metadata extraction
          });
        } catch (sourceError) {
          console.error('Failed to add source:', sourceError);
          // Don't fail the whole flow if source creation fails
        }
      }

      // Step 3: Invite collaborator if email was provided
      if (finalCollaboratorEmail) {
        try {
          await inviteVaultMember(vault.id, {
            email: finalCollaboratorEmail,
            role: VaultRole.CONTRIBUTOR,
          });
        } catch (inviteError) {
          console.error('Failed to invite collaborator:', inviteError);
          // Don't fail the whole flow if invite fails
        }
      }

      // Step 4: Update onboarding state to advance to tutorial
      await updateOnboarding({
        step: 'tutorial',
        data: {
          vaultName: finalVaultName,
          sourceUrl: finalSourceUrl,
          collaboratorEmail: finalCollaboratorEmail,
          createdVaultId: vault.id,
        },
      });
    } catch (error) {
      console.error('Failed to create vault:', error);
      setCreationError(
        error instanceof Error
          ? error.message
          : 'Failed to create vault. Please try again.'
      );
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
    <div className="w-full max-w-2xl mx-auto p-4 md:p-6">
      {/* Progress Indicator */}
      <div className="mb-6 md:mb-8">
        <div className="flex items-center justify-center gap-1.5 md:gap-2 mb-2">
          <div className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center font-bold text-xs md:text-sm ${
            currentStep >= 1
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
              : 'bg-white/10 text-[#94A3B8]'
          }`}>
            1
          </div>
          <div className={`w-12 md:w-16 h-1 ${currentStep >= 2 ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]' : 'bg-white/10'}`} />
          <div className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center font-bold text-xs md:text-sm ${
            currentStep >= 2
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
              : 'bg-white/10 text-[#94A3B8]'
          }`}>
            2
          </div>
          <div className={`w-12 md:w-16 h-1 ${currentStep >= 3 ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]' : 'bg-white/10'}`} />
          <div className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center font-bold text-xs md:text-sm ${
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
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 md:p-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Name Your Vault</h2>
          <p className="text-sm md:text-base text-[#94A3B8] mb-6 md:mb-8">
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
              className="min-h-[44px]"
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
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 md:p-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Add Your First Source</h2>
          <p className="text-sm md:text-base text-[#94A3B8] mb-6 md:mb-8">
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

          <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3">
            <button
              onClick={handleStep2Back}
              disabled={isSubmitting}
              className="text-[#94A3B8] hover:text-white transition-colors px-4 py-2 min-h-[44px] order-2 md:order-1"
            >
              Back
            </button>
            <div className="flex flex-col-reverse md:flex-row gap-3 md:gap-4 items-stretch md:items-center order-1 md:order-2">
              <button
                onClick={handleStep2Skip}
                disabled={isSubmitting}
                className="text-[#94A3B8] hover:text-white transition-colors text-sm underline py-2 min-h-[44px]"
              >
                Skip this step
              </button>
              <GradientButton
                onClick={handleStep2Next}
                disabled={isSubmitting}
                isLoading={isSubmitting}
                className="min-h-[44px]"
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

      {/* Step 3: Invite Collaborator */}
      {currentStep === 3 && (
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 md:p-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Invite a Collaborator</h2>
          <p className="text-sm md:text-base text-[#94A3B8] mb-6 md:mb-8">
            Research is better together! Invite a teammate to collaborate on your vault (optional).
          </p>

          <div className="mb-8">
            <label htmlFor="collaborator-email" className="block text-white font-semibold mb-3">
              Collaborator Email (Optional)
            </label>
            <input
              id="collaborator-email"
              type="email"
              value={collaboratorEmail}
              onChange={(e) => {
                setCollaboratorEmail(e.target.value);
                setEmailError(null);
                setCreationError(null);
              }}
              onKeyDown={handleKeyDown}
              placeholder="colleague@university.edu"
              className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-[#94A3B8]/50 focus:border-[#F7931A] focus:outline-none transition-colors"
              autoFocus
            />
            {emailError && (
              <p className="mt-2 text-sm text-red-400">{emailError}</p>
            )}
            {creationError && (
              <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <p className="text-sm text-red-400">{creationError}</p>
              </div>
            )}
          </div>

          <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3">
            <button
              onClick={handleStep3Back}
              disabled={isSubmitting}
              className="text-[#94A3B8] hover:text-white transition-colors px-4 py-2 min-h-[44px] order-2 md:order-1"
            >
              Back
            </button>
            <div className="flex flex-col-reverse md:flex-row gap-3 md:gap-4 items-stretch md:items-center order-1 md:order-2">
              <button
                onClick={handleStep3Skip}
                disabled={isSubmitting}
                className="text-[#94A3B8] hover:text-white transition-colors text-sm underline py-2 min-h-[44px]"
              >
                Skip
              </button>
              <GradientButton
                onClick={() => handleCreateVault()}
                disabled={isSubmitting}
                isLoading={isSubmitting}
                className="min-h-[44px]"
              >
                Create Vault
              </GradientButton>
            </div>
          </div>

          {/* Helpful Tip */}
          <div className="mt-6 text-center text-[#94A3B8] text-sm">
            💡 Tip: Collaborators can add sources, create annotations, and help build your research vault
          </div>
        </div>
      )}
    </div>
  );
};

export default GuidedVaultWizard;
