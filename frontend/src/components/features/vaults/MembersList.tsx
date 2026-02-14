'use client';

import { useState } from 'react';
import { useVaultMembers } from '@/hooks/useVaultMembers';
import { VaultRole } from '@/lib/types/vault';
import { Badge } from '@/components/ui/badge';
import { Users, UserPlus } from 'lucide-react';
import { cn } from '@/lib/utils';
import GradientButton from '@/components/ui/GradientButton';
import AddMemberModal from './AddMemberModal';

interface MembersListProps {
  vaultId: number;
  userRole?: VaultRole;
}

// Get role badge colors
function getRoleBadgeStyles(role: VaultRole) {
  switch (role) {
    case VaultRole.OWNER:
      return 'bg-primary/20 text-primary border-primary/30';
    case VaultRole.CONTRIBUTOR:
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case VaultRole.VIEWER:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

// Get user initials from name
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

// Sort members: Owner first, then alphabetically
function sortMembers(members: any[]) {
  return [...members].sort((a, b) => {
    // Owners come first
    if (a.role === VaultRole.OWNER && b.role !== VaultRole.OWNER) return -1;
    if (a.role !== VaultRole.OWNER && b.role === VaultRole.OWNER) return 1;
    // Then alphabetically by name
    return a.user_name.localeCompare(b.user_name);
  });
}

export function MembersList({ vaultId, userRole }: MembersListProps) {
  const { data: membersResponse, isLoading, error } = useVaultMembers(vaultId);
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);

  // Extract members from paginated response
  const members = membersResponse?.results || [];
  const sortedMembers = sortMembers(members);

  // Check if user is owner
  const isOwner = userRole === VaultRole.OWNER;

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-white/5" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-white/5 rounded w-1/3" />
                <div className="h-3 bg-white/5 rounded w-1/2" />
              </div>
              <div className="h-6 w-24 bg-white/5 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">Failed to load members</p>
      </div>
    );
  }

  // Empty state (unlikely for members, but good to have)
  if (sortedMembers.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <Users className="w-8 h-8 text-[#F7931A]" />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">No members</h3>
        <p className="text-[#94A3B8]">This vault has no members yet</p>
      </div>
    );
  }

  return (
    <>
      {/* Add Member button (only for owners) */}
      {isOwner && (
        <div className="mb-6">
          <GradientButton onClick={() => setIsAddMemberModalOpen(true)}>
            <UserPlus className="w-5 h-5 mr-2" />
            Add Member
          </GradientButton>
        </div>
      )}

      <div className="space-y-4">
        {sortedMembers.map((member) => (
        <div
          key={member.id}
          className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all"
        >
          <div className="flex items-center gap-4">
            {/* Avatar with initials */}
            <div className="w-12 h-12 bg-gradient-to-br from-[#F7931A] to-[#EA580C] rounded-full flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-lg">
                {getInitials(member.user_name)}
              </span>
            </div>

            {/* Member info */}
            <div className="flex-1 min-w-0">
              <h3 className="text-white font-semibold text-lg truncate">
                {member.user_name}
              </h3>
              <p className="text-[#94A3B8] text-sm truncate">
                {member.user_email}
              </p>
            </div>

            {/* Role badge */}
            <Badge className={cn('shrink-0', getRoleBadgeStyles(member.role))}>
              {member.role}
            </Badge>

            {/* Pending status badge (if applicable) */}
            {member.is_pending && (
              <Badge className="shrink-0 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                Pending
              </Badge>
            )}
          </div>
        </div>
      ))}
      </div>

      {/* Add Member Modal */}
      <AddMemberModal
        vaultId={vaultId}
        isOpen={isAddMemberModalOpen}
        onClose={() => setIsAddMemberModalOpen(false)}
      />
    </>
  );
}
