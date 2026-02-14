'use client';

import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tabs from '@radix-ui/react-tabs';
import { X, UserPlus, Mail } from 'lucide-react';
import { useAddMember, useInviteMember } from '@/hooks/useVaultMembers';
import { VaultRole } from '@/lib/types/vault';
import GradientButton from '@/components/ui/GradientButton';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/useToast';

interface AddMemberModalProps {
  vaultId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function AddMemberModal({ vaultId, isOpen, onClose }: AddMemberModalProps) {
  const [activeTab, setActiveTab] = useState('add-existing');

  // Add Existing User state
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<VaultRole>(VaultRole.CONTRIBUTOR);

  // Invite New User state
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<VaultRole>(VaultRole.CONTRIBUTOR);

  const [error, setError] = useState('');

  const { mutate: addMember, isPending: isAddingMember } = useAddMember(vaultId);
  const { mutate: inviteMember, isPending: isInvitingMember } = useInviteMember(vaultId);
  const { toast } = useToast();

  const handleAddExisting = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email or username is required');
      return;
    }

    addMember(
      { email: email.trim(), role },
      {
        onSuccess: () => {
          toast({
            title: 'Member added',
            description: `${email} has been added to the vault`,
          });
          setEmail('');
          setRole(VaultRole.CONTRIBUTOR);
          onClose();
        },
        onError: (err: any) => {
          setError(err?.response?.data?.error || 'User not found or already a member');
        },
      }
    );
  };

  const handleInviteNew = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!inviteEmail.trim()) {
      setError('Email is required');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(inviteEmail.trim())) {
      setError('Please enter a valid email address');
      return;
    }

    inviteMember(
      { email: inviteEmail.trim(), role: inviteRole },
      {
        onSuccess: () => {
          toast({
            title: 'Invitation sent',
            description: `Invitation sent to ${inviteEmail}`,
          });
          setInviteEmail('');
          setInviteRole(VaultRole.CONTRIBUTOR);
          onClose();
        },
        onError: (err: any) => {
          setError(err?.response?.data?.error || 'Failed to send invitation');
        },
      }
    );
  };

  const handleClose = () => {
    setEmail('');
    setInviteEmail('');
    setRole(VaultRole.CONTRIBUTOR);
    setInviteRole(VaultRole.CONTRIBUTOR);
    setError('');
    setActiveTab('add-existing');
    onClose();
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-[#0F1115] backdrop-blur-lg border border-white/10 rounded-2xl p-8 shadow-[0_0_40px_-10px_rgba(247,147,26,0.3)] z-50">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-2xl font-bold text-white">Add Member</Dialog.Title>
            <Dialog.Close asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-white/60 hover:text-white hover:bg-white/5 w-9 h-9 p-0"
              >
                <X className="w-5 h-5" />
              </Button>
            </Dialog.Close>
          </div>

          <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
            <Tabs.List className="flex gap-4 border-b border-white/10 mb-6">
              <Tabs.Trigger
                value="add-existing"
                className="pb-3 px-2 text-sm font-medium text-white/60 relative transition-colors data-[state=active]:text-white"
              >
                <div className="flex items-center gap-2">
                  <UserPlus className="w-4 h-4" />
                  Add Existing
                </div>
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity"
                  data-state={activeTab === 'add-existing' ? 'active' : 'inactive'}
                />
              </Tabs.Trigger>

              <Tabs.Trigger
                value="invite-new"
                className="pb-3 px-2 text-sm font-medium text-white/60 relative transition-colors data-[state=active]:text-white"
              >
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Invite New
                </div>
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity"
                  data-state={activeTab === 'invite-new' ? 'active' : 'inactive'}
                />
              </Tabs.Trigger>
            </Tabs.List>

            {/* Add Existing User Tab */}
            <Tabs.Content value="add-existing">
              <form onSubmit={handleAddExisting} className="space-y-6">
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-white/80">
                    Email or Username
                  </label>
                  <Input
                    id="email"
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter email or username"
                    className="w-full"
                    disabled={isAddingMember}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="role" className="text-sm font-medium text-white/80">
                    Role
                  </label>
                  <select
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value as VaultRole)}
                    className="w-full bg-black/50 border border-white/20 rounded-lg h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none"
                    disabled={isAddingMember}
                  >
                    <option value={VaultRole.CONTRIBUTOR}>Contributor</option>
                    <option value={VaultRole.VIEWER}>Viewer</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleClose}
                    disabled={isAddingMember}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <GradientButton
                    type="submit"
                    disabled={isAddingMember || !email.trim()}
                    className="flex-1"
                  >
                    {isAddingMember ? 'Adding...' : 'Add Member'}
                  </GradientButton>
                </div>
              </form>
            </Tabs.Content>

            {/* Invite New User Tab */}
            <Tabs.Content value="invite-new">
              <form onSubmit={handleInviteNew} className="space-y-6">
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <label htmlFor="invite-email" className="text-sm font-medium text-white/80">
                    Email Address
                  </label>
                  <Input
                    id="invite-email"
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full"
                    disabled={isInvitingMember}
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="invite-role" className="text-sm font-medium text-white/80">
                    Role
                  </label>
                  <select
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as VaultRole)}
                    className="w-full bg-black/50 border border-white/20 rounded-lg h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none"
                    disabled={isInvitingMember}
                  >
                    <option value={VaultRole.CONTRIBUTOR}>Contributor</option>
                    <option value={VaultRole.VIEWER}>Viewer</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleClose}
                    disabled={isInvitingMember}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <GradientButton
                    type="submit"
                    disabled={isInvitingMember || !inviteEmail.trim()}
                    className="flex-1"
                  >
                    {isInvitingMember ? 'Sending...' : 'Send Invite'}
                  </GradientButton>
                </div>
              </form>
            </Tabs.Content>
          </Tabs.Root>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
