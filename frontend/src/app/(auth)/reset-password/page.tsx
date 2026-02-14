'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { FormInput } from '@/components/ui/FormInput';
import GradientButton from '@/components/ui/GradientButton';
import GlassCard from '@/components/ui/GlassCard';
import { PasswordStrength } from '@/components/ui/PasswordStrength';
import { api } from '@/lib/api';
import { toast } from '@/hooks/useToast';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    password?: string;
    confirmPassword?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [tokenError, setTokenError] = useState(false);

  // Check if token exists on mount
  useEffect(() => {
    if (!token) {
      setTokenError(true);
    }
  }, [token]);

  // Validate form
  const validate = (): boolean => {
    const newErrors: {
      password?: string;
      confirmPassword?: string;
    } = {};

    // Password validation
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    // Confirm password validation
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (confirmPassword !== password) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (!validate()) {
      return;
    }

    if (!token) {
      toast({
        title: 'Invalid Token',
        description: 'Password reset token is missing.',
      });
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/auth/password-reset/confirm/', {
        token,
        password,
      });

      // Show success toast
      toast({
        title: 'Password Reset',
        description: 'Your password has been successfully reset. Redirecting to login...',
      });

      // Redirect to login after short delay
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (err: any) {
      // Check if token is invalid/expired
      const errorMessage = err.response?.data?.error || 'Failed to reset password';

      if (errorMessage.toLowerCase().includes('token') ||
          errorMessage.toLowerCase().includes('expired') ||
          errorMessage.toLowerCase().includes('invalid')) {
        setTokenError(true);
      }

      toast({
        title: 'Reset Failed',
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Show error state if token is missing or invalid
  if (tokenError) {
    return (
      <GlassCard className="w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Invalid Reset Link
          </h1>
        </div>

        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center space-y-4">
          <p className="text-red-400 font-semibold">Reset Link Invalid or Expired</p>
          <p className="text-[#94A3B8] text-sm">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
          <Link href="/forgot-password">
            <GradientButton className="mt-4">
              Request New Reset Link
            </GradientButton>
          </Link>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/login"
            className="text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors"
          >
            ← Back to login
          </Link>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
          Set New Password
        </h1>
        <p className="text-[#94A3B8] text-sm">
          Enter your new password below
        </p>
      </div>

      {/* Reset Password Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* New Password Input with Strength Indicator */}
        <div>
          <FormInput
            label="New Password"
            type="password"
            placeholder="Enter new password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
          />
          <PasswordStrength password={password} />
        </div>

        {/* Confirm Password Input */}
        <FormInput
          label="Confirm Password"
          type="password"
          placeholder="Confirm your password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={errors.confirmPassword}
        />

        {/* Submit Button */}
        <GradientButton type="submit" className="w-full" isLoading={isLoading}>
          Reset Password
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
    </GlassCard>
  );
}
