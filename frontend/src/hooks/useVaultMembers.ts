import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getVaultMembers,
  addVaultMember,
  inviteVaultMember,
  updateMemberRole,
  removeMember,
} from '@/lib/api/vaults';
import type {
  VaultMember,
  VaultMembersListResponse,
  AddMemberRequest,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
} from '@/lib/types/vault';

/**
 * Query key factory for vault members
 */
export const vaultMemberKeys = {
  all: ['vaultMembers'] as const,
  lists: () => [...vaultMemberKeys.all, 'list'] as const,
  list: (vaultId: number) => [...vaultMemberKeys.lists(), vaultId] as const,
};

/**
 * Hook to fetch all members of a vault
 */
export const useVaultMembers = (vaultId: number) => {
  return useQuery<VaultMembersListResponse>({
    queryKey: vaultMemberKeys.list(vaultId),
    queryFn: () => getVaultMembers(vaultId),
    enabled: !!vaultId,
  });
};

/**
 * Hook to add an existing user to a vault by email/username
 */
export const useAddMember = (vaultId: number) => {
  const queryClient = useQueryClient();

  return useMutation<VaultMember, Error, AddMemberRequest>({
    mutationFn: (data) => addVaultMember(vaultId, data),
    onSuccess: () => {
      // Invalidate members list to refetch
      queryClient.invalidateQueries({ queryKey: vaultMemberKeys.list(vaultId) });
    },
  });
};

/**
 * Hook to invite a new user by email (sends email invitation)
 */
export const useInviteMember = (vaultId: number) => {
  const queryClient = useQueryClient();

  return useMutation<VaultMember, Error, InviteMemberRequest>({
    mutationFn: (data) => inviteVaultMember(vaultId, data),
    onSuccess: () => {
      // Invalidate members list to show pending invite
      queryClient.invalidateQueries({ queryKey: vaultMemberKeys.list(vaultId) });
    },
  });
};

/**
 * Hook to update a member's role in a vault
 */
export const useUpdateRole = (vaultId: number) => {
  const queryClient = useQueryClient();

  return useMutation<VaultMember, Error, { memberId: number; data: UpdateMemberRoleRequest }>({
    mutationFn: ({ memberId, data }) => updateMemberRole(vaultId, memberId, data),
    onSuccess: () => {
      // Invalidate members list to show updated role
      queryClient.invalidateQueries({ queryKey: vaultMemberKeys.list(vaultId) });
    },
  });
};

/**
 * Hook to remove a member from a vault
 */
export const useRemoveMember = (vaultId: number) => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (memberId) => removeMember(vaultId, memberId),
    onSuccess: () => {
      // Invalidate members list to remove the member
      queryClient.invalidateQueries({ queryKey: vaultMemberKeys.list(vaultId) });
    },
  });
};
