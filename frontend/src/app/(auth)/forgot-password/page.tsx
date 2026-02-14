'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FormInput } from '@/components/ui/FormInput';
import GradientButton from '@/components/ui/GradientButton';
import GlassCard from '@/components/ui/GlassCard';
import { api } from '@/lib/api';
import { toast } from '@/hooks/useToast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Validate email format
  const validateEmail = (email: string): boolean => {
    if (!email) {
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate email
    if (!email) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      await api.post('/auth/password-reset/', { email });

      // Show success message
      setIsSuccess(true);
      toast({
        title: 'Reset Link Sent',
        description: 'Check your email for password reset instructions.',
      });
    } catch (err: any) {
      // Show error toast
      toast({
        title: 'Request Failed',
        description: err.response?.data?.error || 'Failed to send reset link. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
          Reset Password
        </h1>
        <p className="text-[#94A3B8] text-sm">
          Enter your email and we'll send you a reset link
        </p>
      </div>

      {isSuccess ? (
        // Success message
        <div className="space-y-6">
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
            <p className="text-green-400 font-semibold mb-2">Check Your Email</p>
            <p className="text-[#94A3B8] text-sm">
              We've sent password reset instructions to <strong className="text-white">{email}</strong>
            </p>
          </div>

          <Link
            href="/login"
            className="block text-center text-[#F7931A] hover:text-[#FFD600] transition-colors font-semibold"
          >
            Back to login
          </Link>
        </div>
      ) : (
        // Form
        <>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input */}
            <FormInput
              label="Email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={error}
            />

            {/* Submit Button */}
            <GradientButton type="submit" className="w-full" isLoading={isLoading}>
              Send Reset Link
            </GradientButton>
          </form>

          {/* Back to Login Link */}
          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors"
            >
              ← Back to login
            </Link>
          </div>
        </>
      )}
    </GlassCard>
  );
}
