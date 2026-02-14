import { VaultRole } from '@/lib/types/vault';

interface VaultPermissions {
  canEdit: boolean;
  canManageMembers: boolean;
  canDelete: boolean;
  isOwner: boolean;
  isContributor: boolean;
  isViewer: boolean;
}

/**
 * Hook to determine user permissions based on their role in a vault
 * @param userRole - The user's role in the vault (OWNER, CONTRIBUTOR, or VIEWER)
 * @returns Object with permission flags
 */
export function useVaultPermissions(userRole: VaultRole): VaultPermissions {
  const isOwner = userRole === VaultRole.OWNER;
  const isContributor = userRole === VaultRole.CONTRIBUTOR;
  const isViewer = userRole === VaultRole.VIEWER;

  return {
    // Edit permissions: Owners and Contributors can edit content
    canEdit: isOwner || isContributor,

    // Member management: Only Owners can add/remove members and change roles
    canManageMembers: isOwner,

    // Delete/Archive: Only Owners can delete or archive vaults
    canDelete: isOwner,

    // Role checks for conditional rendering
    isOwner,
    isContributor,
    isViewer,
  };
}
