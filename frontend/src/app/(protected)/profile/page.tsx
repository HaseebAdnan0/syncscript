'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/stores/authStore';
import { FormInput } from '@/components/ui/FormInput';
import { Textarea } from '@/components/ui/textarea';
import GradientButton from '@/components/ui/GradientButton';
import { useToast } from '@/hooks/useToast';
import { api } from '@/lib/api';
import * as Tabs from '@radix-ui/react-tabs';
import { PasswordStrength } from '@/components/ui/PasswordStrength';

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();

  // Profile form state
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [profileErrors, setProfileErrors] = useState<{ firstName?: string; lastName?: string }>({});

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmNewPassword?: string;
  }>({});

  // Validate profile form
  const validateProfileForm = (): boolean => {
    const errors: typeof profileErrors = {};

    if (!firstName.trim()) {
      errors.firstName = 'First name is required';
    } else if (firstName.trim().length < 2) {
      errors.firstName = 'First name must be at least 2 characters';
    }

    setProfileErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle profile form submission
  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateProfileForm()) {
      return;
    }

    setIsProfileLoading(true);

    try {
      const response = await api.put('/auth/me/', {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        bio: bio.trim(),
      });

      // Update auth store with new user data
      setUser(response.data);

      toast({
        title: 'Success',
        description: 'Profile updated successfully',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Failed to update profile',
      });
    } finally {
      setIsProfileLoading(false);
    }
  };

  // Validate password change form
  const validatePasswordForm = (): boolean => {
    const errors: typeof passwordErrors = {};

    if (!currentPassword.trim()) {
      errors.currentPassword = 'Current password is required';
    }

    if (!newPassword.trim()) {
      errors.newPassword = 'New password is required';
    } else if (newPassword.length < 8) {
      errors.newPassword = 'Password must be at least 8 characters';
    }

    if (!confirmNewPassword.trim()) {
      errors.confirmNewPassword = 'Please confirm your new password';
    } else if (newPassword !== confirmNewPassword) {
      errors.confirmNewPassword = 'Passwords do not match';
    }

    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle password change form submission
  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validatePasswordForm()) {
      return;
    }

    setIsPasswordLoading(true);

    try {
      await api.post('/auth/password-change/', {
        old_password: currentPassword,
        new_password: newPassword,
      });

      // Clear form on success
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      setPasswordErrors({});

      toast({
        title: 'Success',
        description: 'Password updated successfully',
      });
    } catch (error: any) {
      // Check if error is due to wrong current password
      const errorMessage = error.response?.data?.old_password?.[0] ||
                          error.response?.data?.message ||
                          'Failed to update password';

      if (errorMessage.toLowerCase().includes('incorrect') ||
          errorMessage.toLowerCase().includes('wrong')) {
        setPasswordErrors({ currentPassword: errorMessage });
      } else {
        toast({
          title: 'Error',
          description: errorMessage,
        });
      }
    } finally {
      setIsPasswordLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#030304] py-12">
        <div className="max-w-4xl mx-auto px-4">
          {/* Back Navigation */}
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
              Account Settings
            </h1>
            <p className="text-[#94A3B8]">
              Manage your profile information and security settings
            </p>
          </div>

          {/* Tabs Container */}
          <Tabs.Root defaultValue="profile" className="w-full">
            {/* Tab List */}
            <Tabs.List className="flex border-b border-white/10 mb-8">
              <Tabs.Trigger
                value="profile"
                className="px-6 py-3 text-[#94A3B8] font-semibold transition-colors relative data-[state=active]:text-[#F7931A] hover:text-white"
              >
                Profile
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
              </Tabs.Trigger>
              <Tabs.Trigger
                value="security"
                className="px-6 py-3 text-[#94A3B8] font-semibold transition-colors relative data-[state=active]:text-[#F7931A] hover:text-white"
              >
                Security
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
              </Tabs.Trigger>
            </Tabs.List>

            {/* Profile Tab Content */}
            <Tabs.Content value="profile" className="focus:outline-none">
              <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8">
                <h2 className="text-2xl font-heading font-bold text-white mb-6">
                  Profile Information
                </h2>

                <form onSubmit={handleProfileSubmit} className="space-y-6">
                  {/* Email (read-only) */}
                  <FormInput
                    label="Email"
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="opacity-60 cursor-not-allowed"
                  />

                  {/* First Name */}
                  <FormInput
                    label="First Name"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    error={profileErrors.firstName}
                    placeholder="Enter your first name"
                  />

                  {/* Last Name */}
                  <FormInput
                    label="Last Name"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    error={profileErrors.lastName}
                    placeholder="Enter your last name"
                  />

                  {/* Bio (optional textarea) */}
                  <div className="w-full">
                    <label className="block text-sm font-medium text-white/80 mb-2">
                      Bio (Optional)
                    </label>
                    <Textarea
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell us about yourself..."
                      rows={4}
                    />
                  </div>

                  {/* Submit Button */}
                  <div className="pt-4">
                    <GradientButton
                      type="submit"
                      isLoading={isProfileLoading}
                      className="w-full sm:w-auto"
                    >
                      Save Changes
                    </GradientButton>
                  </div>
                </form>
              </div>
            </Tabs.Content>

            {/* Security Tab Content */}
            <Tabs.Content value="security" className="focus:outline-none">
              <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8">
                <h2 className="text-2xl font-heading font-bold text-white mb-6">
                  Security Settings
                </h2>

                <form onSubmit={handlePasswordSubmit} className="space-y-6">
                  {/* Current Password */}
                  <FormInput
                    label="Current Password"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    error={passwordErrors.currentPassword}
                    placeholder="Enter your current password"
                  />

                  {/* New Password */}
                  <div>
                    <FormInput
                      label="New Password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      error={passwordErrors.newPassword}
                      placeholder="Enter your new password (min 8 characters)"
                    />
                    {/* Password Strength Indicator */}
                    <PasswordStrength password={newPassword} />
                  </div>

                  {/* Confirm New Password */}
                  <FormInput
                    label="Confirm New Password"
                    type="password"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    error={passwordErrors.confirmNewPassword}
                    placeholder="Re-enter your new password"
                  />

                  {/* Submit Button */}
                  <div className="pt-4">
                    <GradientButton
                      type="submit"
                      isLoading={isPasswordLoading}
                      className="w-full sm:w-auto"
                    >
                      Update Password
                    </GradientButton>
                  </div>
                </form>
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </div>
      </div>
    </ProtectedRoute>
  );
}
