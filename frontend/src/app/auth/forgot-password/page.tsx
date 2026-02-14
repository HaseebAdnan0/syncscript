'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Mail } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import GradientButton from '@/components/ui/GradientButton';
import { useToast } from '@/hooks/useToast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { toast } = useToast();

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
        <GlassCard className="w-full max-w-md p-8 text-center">
          <Mail className="w-16 h-16 text-[#F7931A] mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-white mb-4">Check Your Email</h1>
          <p className="text-[#94A3B8] mb-6">
            If an account exists with <span className="text-white font-medium">{email}</span>,
            we've sent password reset instructions to that address.
          </p>
          <p className="text-[#94A3B8] text-sm mb-8">
            The link will expire in 1 hour.
          </p>
          <Link href="/login" className="text-[#F7931A] hover:text-[#FFD600] transition-colors flex items-center justify-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to login
          </Link>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304] flex items-center justify-center p-4">
      <GlassCard className="w-full max-w-md p-8">
        <Link
          href="/login"
          className="text-[#94A3B8] hover:text-[#F7931A] transition-colors flex items-center gap-2 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>

        <h1 className="text-3xl font-bold text-white mb-2">Forgot Password?</h1>
        <p className="text-[#94A3B8] mb-8">
          Enter your email address and we'll send you instructions to reset your password.
        </p>

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
            className="w-full"
          >
            {isSubmitting ? 'Sending...' : 'Send Reset Link'}
          </GradientButton>
        </form>
      </GlassCard>
    </div>
  );
}
