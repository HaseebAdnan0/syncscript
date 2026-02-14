'use client';

import { useState } from 'react';
import { useVaultMembers, useUpdateRole, useRemoveMember } from '@/hooks/useVaultMembers';
import { VaultRole } from '@/lib/types/vault';
import { Badge } from '@/components/ui/badge';
import { Users, UserPlus, ChevronDown, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import GradientButton from '@/components/ui/GradientButton';
import AddMemberModal from './AddMemberModal';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/useToast';

interface MembersListProps {
  vaultId: number;
  userRole?: VaultRole;
  currentUserId?: number;
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

export function MembersList({ vaultId, userRole, currentUserId }: MembersListProps) {
  const { data: membersResponse, isLoading, error } = useVaultMembers(vaultId);
  const updateRoleMutation = useUpdateRole(vaultId);
  const removeMemberMutation = useRemoveMember(vaultId);
  const { toast } = useToast();
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [updatingMemberId, setUpdatingMemberId] = useState<number | null>(null);
  const [removingMember, setRemovingMember] = useState<{ id: number; name: string } | null>(null);

  // Extract members from paginated response
  const members = membersResponse?.results || [];
  const sortedMembers = sortMembers(members);

  // Check if user is owner
  const isOwner = userRole === VaultRole.OWNER;

  // Handle role change
  const handleRoleChange = async (memberId: number, newRole: VaultRole) => {
    setUpdatingMemberId(memberId);
    try {
      await updateRoleMutation.mutateAsync({
        memberId,
        data: { role: newRole },
      });
    } catch (error) {
      console.error('Failed to update member role:', error);
    } finally {
      setUpdatingMemberId(null);
    }
  };

  // Handle remove member
  const handleRemoveMember = async () => {
    if (!removingMember) return;

    try {
      await removeMemberMutation.mutateAsync(removingMember.id);
      toast({
        title: 'Member removed',
        description: `${removingMember.name} has been removed from this vault`,
      });
      setRemovingMember(null);
    } catch (error) {
      console.error('Failed to remove member:', error);
      toast({
        title: 'Error',
        description: 'Failed to remove member. Please try again.',
      });
    }
  };

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
        {sortedMembers.map((member) => {
          const isCurrentUser = currentUserId === member.user_id;
          const isMemberOwner = member.role === VaultRole.OWNER;
          const canChangeRole = isOwner && !isMemberOwner && !isCurrentUser;
          const canRemove = isOwner && !isMemberOwner && !isCurrentUser;
          const isUpdating = updatingMemberId === member.id;

          return (
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

                {/* Role dropdown or badge */}
                {canChangeRole ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger
                      disabled={isUpdating}
                      className={cn(
                        'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all',
                        getRoleBadgeStyles(member.role),
                        isUpdating && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      <span className="text-sm font-medium">
                        {isUpdating ? 'Updating...' : member.role}
                      </span>
                      <ChevronDown className="w-4 h-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleRoleChange(member.id, VaultRole.CONTRIBUTOR)}
                        className={cn(
                          member.role === VaultRole.CONTRIBUTOR && 'bg-white/10'
                        )}
                      >
                        Contributor
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleRoleChange(member.id, VaultRole.VIEWER)}
                        className={cn(
                          member.role === VaultRole.VIEWER && 'bg-white/10'
                        )}
                      >
                        Viewer
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <Badge className={cn('shrink-0', getRoleBadgeStyles(member.role))}>
                    {member.role}
                  </Badge>
                )}

                {/* Pending status badge (if applicable) */}
                {member.is_pending && (
                  <Badge className="shrink-0 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                    Pending
                  </Badge>
                )}

                {/* Remove button (only for owners, not for other owners or self) */}
                {canRemove && (
                  <button
                    onClick={() => setRemovingMember({ id: member.id, name: member.user_name })}
                    className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors"
                    aria-label={`Remove ${member.user_name}`}
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Member Modal */}
      <AddMemberModal
        vaultId={vaultId}
        isOpen={isAddMemberModalOpen}
        onClose={() => setIsAddMemberModalOpen(false)}
      />

      {/* Remove Member Confirmation Dialog */}
      <Dialog open={!!removingMember} onOpenChange={(open) => !open && setRemovingMember(null)}>
        <DialogContent className="bg-[#0F1115] border border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white">Remove Member</DialogTitle>
            <DialogDescription className="text-[#94A3B8]">
              Remove {removingMember?.name} from this vault?
            </DialogDescription>
          </DialogHeader>
          <p className="text-[#94A3B8] text-sm">
            They will lose access to all sources and annotations in this vault. This action cannot be undone.
          </p>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setRemovingMember(null)}
              disabled={removeMemberMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleRemoveMember}
              disabled={removeMemberMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {removeMemberMutation.isPending ? 'Removing...' : 'Remove Member'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
