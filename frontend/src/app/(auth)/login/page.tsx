'use client';

import Link from 'next/link';
import { FormInput } from '@/components/ui/FormInput';
import GradientButton from '@/components/ui/GradientButton';
import GlassCard from '@/components/ui/GlassCard';

export default function LoginPage() {
  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
          Welcome Back
        </h1>
        <p className="text-[#94A3B8] text-sm">
          Sign in to access your Knowledge Vaults
        </p>
      </div>

      {/* Login Form */}
      <form className="space-y-6">
        {/* Email Input */}
        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
        />

        {/* Password Input */}
        <FormInput
          label="Password"
          type="password"
          placeholder="Enter your password"
          autoComplete="current-password"
        />

        {/* Forgot Password Link */}
        <div className="flex justify-end">
          <Link
            href="/forgot-password"
            className="text-sm text-[#F7931A] hover:text-[#FFD600] transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        {/* Submit Button */}
        <GradientButton type="submit" className="w-full">
          Sign In
        </GradientButton>
      </form>

      {/* Register Link */}
      <div className="mt-6 text-center">
        <p className="text-sm text-[#94A3B8]">
          Don&apos;t have an account?{' '}
          <Link
            href="/register"
            className="text-[#F7931A] hover:text-[#FFD600] transition-colors font-semibold"
          >
            Sign up
          </Link>
        </p>
      </div>
    </GlassCard>
  );
}
