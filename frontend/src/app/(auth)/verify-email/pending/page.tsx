'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Mail, ArrowLeft } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { toast } from '@/hooks/useToast';

export default function VerifyEmailPendingPage() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';

  const [countdown, setCountdown] = useState(0);
  const [isResending, setIsResending] = useState(false);

  // Countdown timer effect
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Handle resend verification email
  const handleResend = async () => {
    if (countdown > 0 || !email) {
      return;
    }

    setIsResending(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/resend-verification/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email }),
        }
      );

      if (response.ok) {
        toast({
          title: 'Email Sent',
          description: 'Verification email has been resent. Please check your inbox.',
        });
        // Start 60-second countdown
        setCountdown(60);
      } else if (response.status === 429) {
        toast({
          title: 'Too Many Requests',
          description: 'Please wait a moment before requesting another email.',
          variant: 'destructive',
        });
      } else {
        const data = await response.json();
        toast({
          title: 'Resend Failed',
          description: data.error || 'Failed to resend verification email.',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsResending(false);
    }
  };

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Envelope Icon */}
      <div className="flex justify-center mb-6">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 border border-[#F7931A]/30 flex items-center justify-center">
          <Mail className="w-10 h-10 text-[#F7931A]" />
        </div>
      </div>

      {/* Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
          Check Your Email
        </h1>
        <p className="text-[#94A3B8] text-sm">
          We've sent a verification link to
        </p>
        {email && (
          <p className="text-white font-semibold mt-2 break-all">{email}</p>
        )}
      </div>

      {/* Instructions */}
      <div className="mb-8 space-y-3">
        <p className="text-[#94A3B8] text-sm text-center">
          Click the link in your email to verify your account and start using
          SyncScript.
        </p>
        <p className="text-[#94A3B8] text-xs text-center">
          Didn't receive the email? Check your spam folder.
        </p>
      </div>

      {/* Resend Button */}
      <GradientButton
        onClick={handleResend}
        disabled={countdown > 0 || isResending || !email}
        isLoading={isResending}
        className="w-full mb-4"
      >
        {countdown > 0
          ? `Resend in ${countdown}s`
          : 'Resend Verification Email'}
      </GradientButton>

      {/* Back to Login Link */}
      <Link
        href="/login"
        className="flex items-center justify-center gap-2 text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Login
      </Link>
    </GlassCard>
  );
}
