'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FormInput } from '@/components/ui/FormInput';
import GradientButton from '@/components/ui/GradientButton';
import GlassCard from '@/components/ui/GlassCard';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Title */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
          Create Account
        </h1>
        <p className="text-[#94A3B8] text-sm">
          Join SyncScript and start building Knowledge Vaults
        </p>
      </div>

      {/* Registration Form */}
      <form className="space-y-6">
        {/* Name Input */}
        <FormInput
          label="Name"
          type="text"
          placeholder="Your full name"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* Email Input */}
        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        {/* Password Input */}
        <FormInput
          label="Password"
          type="password"
          placeholder="Create a password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {/* Confirm Password Input */}
        <FormInput
          label="Confirm Password"
          type="password"
          placeholder="Confirm your password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        {/* Submit Button */}
        <GradientButton type="submit" className="w-full">
          Create Account
        </GradientButton>
      </form>

      {/* Login Link */}
      <div className="mt-6 text-center">
        <p className="text-sm text-[#94A3B8]">
          Already have an account?{' '}
          <Link
            href="/login"
            className="text-[#F7931A] hover:text-[#FFD600] transition-colors font-semibold"
          >
            Sign in
          </Link>
        </p>
      </div>
    </GlassCard>
  );
}
