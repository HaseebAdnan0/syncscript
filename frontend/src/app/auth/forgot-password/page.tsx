'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Mail } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { useToast } from '@/hooks/useToast';

export default function ForgotPasswordPage() {
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Basic email validation
    if (!email || !email.includes('@')) {
      toast({
        title: 'Invalid email',
        description: 'Please enter a valid email address',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/password-reset/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email }),
        }
      );

      if (response.ok) {
        setIsSubmitted(true);
        toast({
          title: 'Reset link sent',
          description: 'If an account exists, we\'ve sent a reset link to your email',
        });
      } else {
        const data = await response.json();
        toast({
          title: 'Error',
          description: data.error || 'Failed to send reset link',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
        <GlassCard className="w-full max-w-md p-8">
          {/* Mail Icon */}
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
              If an account exists with
            </p>
            <p className="text-white font-semibold mt-2 break-all">{email}</p>
            <p className="text-[#94A3B8] text-sm mt-2">
              we've sent password reset instructions to that address.
            </p>
          </div>

          {/* Expiry Notice */}
          <div className="mb-8 bg-[#F7931A]/10 border border-[#F7931A]/20 rounded-lg p-4">
            <p className="text-[#94A3B8] text-sm text-center">
              The link will expire in <span className="text-[#F7931A] font-semibold">1 hour</span>.
            </p>
          </div>

          {/* Back to Login Link */}
          <Link
            href="/login"
            className="flex items-center justify-center gap-2 text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Login
          </Link>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
      <GlassCard className="w-full max-w-md p-8">
        {/* Back to Login Link */}
        <Link
          href="/login"
          className="flex items-center gap-2 text-sm text-[#94A3B8] hover:text-[#F7931A] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Login
        </Link>

        {/* Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Forgot Password?
          </h1>
          <p className="text-[#94A3B8] text-sm">
            Enter your email address and we'll send you instructions to reset your password.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors"
              placeholder="you@example.com"
              disabled={isSubmitting}
            />
          </div>

          <GradientButton
            type="submit"
            disabled={isSubmitting}
            isLoading={isSubmitting}
            className="w-full"
          >
            Send Reset Link
          </GradientButton>
        </form>
      </GlassCard>
    </div>
  );
}
