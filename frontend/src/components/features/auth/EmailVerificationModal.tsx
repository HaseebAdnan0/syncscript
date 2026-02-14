'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Mail, X } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { resendVerificationEmail } from '@/lib/api';
import { toast } from '@/hooks/useToast';
import { useAuthStore } from '@/stores/authStore';

interface EmailVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function EmailVerificationModal({ isOpen, onClose }: EmailVerificationModalProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const [isResending, setIsResending] = useState(false);
  const [countdown, setCountdown] = useState(0);

  // Countdown timer for resend button
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [countdown]);

  const handleResendVerification = async () => {
    if (!user?.email) return;

    setIsResending(true);
    try {
      await resendVerificationEmail(user.email);
      toast({
        title: 'Verification email sent',
        description: `Check your inbox at ${user.email}`,
      });
      setCountdown(60); // 60 second cooldown
    } catch (error) {
      toast({
        title: 'Failed to send verification email',
        description: error instanceof Error ? error.message : 'Please try again later',
      });
    } finally {
      setIsResending(false);
    }
  };

  const handleGoToVerificationPage = () => {
    onClose();
    router.push(`/auth/verify-email/pending?email=${user?.email}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-md px-4">
        <GlassCard className="relative">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-white/60 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>

          {/* Icon */}
          <div className="mb-6 flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A]">
              <Mail className="h-10 w-10 text-white" />
            </div>
          </div>

          {/* Title */}
          <h2 className="mb-4 text-center text-2xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            Verify Your Email
          </h2>

          {/* Message */}
          <p className="mb-2 text-center text-white">
            You must verify your email address to access vault content.
          </p>
          <p className="mb-6 text-center text-sm text-[#94A3B8]">
            Check your inbox at <span className="text-white font-medium">{user?.email}</span>
          </p>

          {/* Actions */}
          <div className="space-y-3">
            <GradientButton
              onClick={handleResendVerification}
              disabled={isResending || countdown > 0}
              className="w-full"
            >
              {countdown > 0
                ? `Resend in ${countdown}s`
                : isResending
                ? 'Sending...'
                : 'Resend Verification Email'}
            </GradientButton>

            <button
              onClick={handleGoToVerificationPage}
              className="w-full py-3 text-sm text-[#F7931A] hover:text-[#FFD600] transition-colors"
            >
              Go to Verification Page
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
