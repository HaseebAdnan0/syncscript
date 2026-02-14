'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormInput } from '@/components/ui/FormInput';
import GradientButton from '@/components/ui/GradientButton';
import GlassCard from '@/components/ui/GlassCard';
import { PasswordStrength } from '@/components/ui/PasswordStrength';
import { useAuth } from '@/hooks/useAuth';
import { toast } from '@/hooks/useToast';
import OAuthButtons from '@/components/features/auth/OAuthButtons';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  // Validate email format
  const validateEmail = (email: string): boolean => {
    if (!email) {
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Validate form
  const validate = (): boolean => {
    const newErrors: {
      name?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    // Name validation
    if (!name) {
      newErrors.name = 'Name is required';
    } else if (name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    // Email validation
    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

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

    setIsLoading(true);

    try {
      const result = await register({
        email,
        password,
        username: email, // Use email as username for now
        first_name: name,
      });

      if (result.success) {
        // Show success toast
        toast({
          title: 'Account Created',
          description: 'Welcome to SyncScript! Redirecting to dashboard...',
        });

        // Auto-login and redirect to dashboard
        router.push('/dashboard');
      } else {
        // Show error toast
        toast({
          title: 'Registration Failed',
          description: result.error || 'Failed to create account. Please try again.',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

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

      {/* OAuth Buttons */}
      <OAuthButtons disabled={isLoading} />

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-[#0F1115] text-[#94A3B8]">or</span>
        </div>
      </div>

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name Input */}
        <FormInput
          label="Name"
          type="text"
          placeholder="Your full name"
          autoComplete="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />

        {/* Email Input */}
        <FormInput
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
        />

        {/* Password Input with Strength Indicator */}
        <div>
          <FormInput
            label="Password"
            type="password"
            placeholder="Create a password"
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
