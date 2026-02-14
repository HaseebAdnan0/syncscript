'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import Link from 'next/link';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { confirmPasswordReset } from '@/lib/api';
import { toast } from '@/hooks/useToast';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const uid = searchParams.get('uid');
  const token = searchParams.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Password strength validation
  const passwordRequirements = {
    minLength: newPassword.length >= 8,
    hasUpperCase: /[A-Z]/.test(newPassword),
    hasLowerCase: /[a-z]/.test(newPassword),
    hasNumber: /[0-9]/.test(newPassword),
  };

  const passwordsMatch = newPassword === confirmPassword && confirmPassword !== '';
  const isPasswordValid = Object.values(passwordRequirements).every(Boolean);

  // Redirect to login after 3 seconds on success
  useEffect(() => {
    if (isSuccess) {
      const timer = setTimeout(() => {
        router.push('/login');
      }, 3000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [isSuccess, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!uid || !token) {
      setError('Invalid reset link. Please request a new password reset.');
      return;
    }

    if (!isPasswordValid) {
      setError('Password does not meet requirements.');
      return;
    }

    if (!passwordsMatch) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      await confirmPasswordReset(uid, token, newPassword);
      setIsSuccess(true);
      toast({
        title: 'Password Reset Successful',
        description: 'You can now log in with your new password.',
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset password. The link may have expired.';
      setError(errorMessage);
      toast({
        title: 'Reset Failed',
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Success state
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
        <GlassCard className="w-full max-w-md p-8 text-center">
          <div className="mb-6 flex justify-center">
            <div className="rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] p-3">
              <CheckCircle className="h-12 w-12 text-white" />
            </div>
          </div>

          <h1 className="text-3xl font-bold mb-4 bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            Password Reset Complete
          </h1>

          <p className="text-[#94A3B8] mb-6">
            Your password has been successfully reset. You will be redirected to login in 3 seconds.
          </p>

          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-[#F7931A] hover:text-[#FFD600] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Go to Login Now
          </Link>
        </GlassCard>
      </div>
    );
  }

  // Error state (link expired or invalid)
  if (error && (error.includes('expired') || error.includes('Invalid'))) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
        <GlassCard className="w-full max-w-md p-8 text-center">
          <div className="mb-6 flex justify-center">
            <div className="rounded-full bg-red-500/20 p-3">
              <XCircle className="h-12 w-12 text-red-500" />
            </div>
          </div>

          <h1 className="text-3xl font-bold mb-4 text-white">
            Reset Link Expired
          </h1>

          <p className="text-[#94A3B8] mb-6">
            {error}
          </p>

          <Link href="/auth/forgot-password">
            <GradientButton className="w-full mb-4">
              Request New Link
            </GradientButton>
          </Link>

          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-[#F7931A] hover:text-[#FFD600] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Login
          </Link>
        </GlassCard>
      </div>
    );
  }

  // Form state
  return (
    <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
      <GlassCard className="w-full max-w-md p-8">
        <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
          Reset Your Password
        </h1>
        <p className="text-[#94A3B8] mb-6">
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* New Password Input */}
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-white mb-2">
              New Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="newPassword"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder:text-[#94A3B8]/50 focus:border-[#F7931A] focus:outline-none transition-colors"
                placeholder="Enter new password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          {/* Confirm Password Input */}
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-white mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 pr-12 text-white placeholder:text-[#94A3B8]/50 focus:border-[#F7931A] focus:outline-none transition-colors"
                placeholder="Confirm new password"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-white transition-colors"
              >
                {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
            {confirmPassword && (
              <p className={`mt-2 text-sm ${passwordsMatch ? 'text-green-500' : 'text-red-500'}`}>
                {passwordsMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
              </p>
            )}
          </div>

          {/* Password Strength Indicator */}
          {newPassword && (
            <div className="bg-black/30 border border-white/10 rounded-lg p-4">
              <p className="text-sm font-medium text-white mb-2">Password Requirements:</p>
              <ul className="space-y-1 text-sm">
                <li className={passwordRequirements.minLength ? 'text-green-500' : 'text-[#94A3B8]'}>
                  {passwordRequirements.minLength ? '✓' : '○'} At least 8 characters
                </li>
                <li className={passwordRequirements.hasUpperCase ? 'text-green-500' : 'text-[#94A3B8]'}>
                  {passwordRequirements.hasUpperCase ? '✓' : '○'} One uppercase letter
                </li>
                <li className={passwordRequirements.hasLowerCase ? 'text-green-500' : 'text-[#94A3B8]'}>
                  {passwordRequirements.hasLowerCase ? '✓' : '○'} One lowercase letter
                </li>
                <li className={passwordRequirements.hasNumber ? 'text-green-500' : 'text-[#94A3B8]'}>
                  {passwordRequirements.hasNumber ? '✓' : '○'} One number
                </li>
              </ul>
            </div>
          )}

          {/* Submit Button */}
          <GradientButton
            type="submit"
            className="w-full"
            isLoading={isLoading}
            disabled={!isPasswordValid || !passwordsMatch}
          >
            Reset Password
          </GradientButton>

          {/* Back to Login */}
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-[#F7931A] hover:text-[#FFD600] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Login
          </Link>
        </form>
      </GlassCard>
    </div>
  );
}
