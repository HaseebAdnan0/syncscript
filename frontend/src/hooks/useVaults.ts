import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getVaults,
  getVault,
  createVault,
  updateVault,
  deleteVault,
  archiveVault,
} from '@/lib/api/vaults';
import {
  Vault,
  CreateVaultRequest,
  UpdateVaultRequest,
  VaultsListResponse,
} from '@/lib/types/vault';

// Query keys
export const vaultKeys = {
  all: ['vaults'] as const,
  lists: () => [...vaultKeys.all, 'list'] as const,
  list: (search?: string) => [...vaultKeys.lists(), { search }] as const,
  details: () => [...vaultKeys.all, 'detail'] as const,
  detail: (id: number) => [...vaultKeys.details(), id] as const,
};

/**
 * Fetch all vaults with optional search filtering
 */
export function useVaults(search?: string) {
  return useQuery<VaultsListResponse, Error>({
    queryKey: vaultKeys.list(search),
    queryFn: () => getVaults(search),
  });
}

/**
 * Fetch a single vault by ID
 */
export function useVault(id: number) {
  return useQuery<Vault, Error>({
    queryKey: vaultKeys.detail(id),
    queryFn: () => getVault(id),
    enabled: !!id,
  });
}

/**
 * Create a new vault
 */
export function useCreateVault() {
  const queryClient = useQueryClient();

  return useMutation<Vault, Error, CreateVaultRequest>({
    mutationFn: createVault,
    onSuccess: () => {
      // Invalidate all vault lists to refetch with new vault
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() });
    },
  });
}

/**
 * Update an existing vault
 */
export function useUpdateVault(id: number) {
  const queryClient = useQueryClient();

  return useMutation<Vault, Error, UpdateVaultRequest>({
    mutationFn: (data) => updateVault(id, data),
    onSuccess: (updatedVault) => {
      // Update the specific vault in cache
      queryClient.setQueryData(vaultKeys.detail(id), updatedVault);
      // Invalidate lists to reflect changes
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() });
    },
  });
}

/**
 * Delete a vault permanently
 */
export function useDeleteVault() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: deleteVault,
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: vaultKeys.detail(deletedId) });
      // Invalidate lists to reflect deletion
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() });
    },
  });
}

/**
 * Archive a vault (soft delete)
 */
export function useArchiveVault(id: number) {
  const queryClient = useQueryClient();

  return useMutation<Vault, Error, void>({
    mutationFn: () => archiveVault(id),
    onSuccess: (archivedVault) => {
      // Update the specific vault in cache
      queryClient.setQueryData(vaultKeys.detail(id), archivedVault);
      // Invalidate lists to reflect archive status
      queryClient.invalidateQueries({ queryKey: vaultKeys.lists() });
    },
  });
}
