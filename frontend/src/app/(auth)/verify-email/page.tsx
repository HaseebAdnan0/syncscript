'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, XCircle, Mail } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { verifyEmail } from '@/lib/api';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error');
        setErrorMessage('Verification token is missing.');
        return;
      }

      try {
        await verifyEmail(token);
        setStatus('success');

        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } catch (error) {
        setStatus('error');
        if (error instanceof Error) {
          setErrorMessage(error.message || 'Failed to verify email. The link may be expired or invalid.');
        } else {
          setErrorMessage('Failed to verify email. The link may be expired or invalid.');
        }
      }
    };

    verify();
  }, [token, router]);

  // Loading state
  if (status === 'loading') {
    return (
      <GlassCard className="w-full max-w-md p-8">
        <div className="flex flex-col items-center gap-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 border border-[#F7931A]/30 flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-[#F7931A] border-t-transparent rounded-full animate-spin" />
          </div>
          <h1 className="text-2xl font-heading font-bold text-white text-center">
            Verifying Your Email...
          </h1>
          <p className="text-[#94A3B8] text-sm text-center">
            Please wait while we verify your email address.
          </p>
        </div>
      </GlassCard>
    );
  }

  // Success state
  if (status === 'success') {
    return (
      <GlassCard className="w-full max-w-md p-8">
        {/* Success Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-500/20 to-green-400/20 border border-green-500/30 flex items-center justify-center">
            <CheckCircle className="w-10 h-10 text-green-500" />
          </div>
        </div>

        {/* Title */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Email Verified!
          </h1>
          <p className="text-[#94A3B8] text-sm">
            Your email has been successfully verified.
          </p>
        </div>

        {/* Success Message */}
        <div className="mb-8 space-y-3">
          <p className="text-white text-center">
            Welcome to SyncScript! Your account is now active.
          </p>
          <p className="text-[#94A3B8] text-xs text-center">
            Redirecting to login in 3 seconds...
          </p>
        </div>

        {/* Continue to Login Button */}
        <Link href="/login">
          <GradientButton className="w-full">
            Continue to Login
          </GradientButton>
        </Link>
      </GlassCard>
    );
  }

  // Error state
  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Error Icon */}
      <div className="flex justify-center mb-6">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-red-500/20 to-red-400/20 border border-red-500/30 flex items-center justify-center">
          <XCircle className="w-10 h-10 text-red-500" />
        </div>
      </div>

      {/* Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold text-white mb-2">
          Verification Failed
        </h1>
        <p className="text-[#94A3B8] text-sm">
          We couldn't verify your email address.
        </p>
      </div>

      {/* Error Message */}
      <div className="mb-8 space-y-3">
        <p className="text-red-400 text-sm text-center">
          {errorMessage}
        </p>
        <p className="text-[#94A3B8] text-xs text-center">
          The verification link may have expired or already been used.
        </p>
      </div>

      {/* Resend Verification Button */}
      <Link href="/verify-email/pending">
        <GradientButton className="w-full mb-4">
          <Mail className="w-5 h-5 mr-2 inline" />
          Resend Verification Email
        </GradientButton>
      </Link>

      {/* Back to Login Link */}
      <Link
        href="/login"
        className="block text-center text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors"
      >
        Back to Login
      </Link>
    </GlassCard>
  );
}
