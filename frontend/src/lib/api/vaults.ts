import { api } from '../api';
import {
  Vault,
  VaultsListResponse,
  CreateVaultRequest,
  UpdateVaultRequest,
  VaultMember,
  VaultMembersListResponse,
  AddMemberRequest,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
  VaultInsights,
  Conversation,
  ConversationDetail,
  AskQuestionRequest,
  AskQuestionResponse,
} from '../types/vault';

export interface GetVaultsParams {
  search?: string;
  ownership?: 'owned' | 'shared';
}

/**
 * Get all vaults for the current user
 * @param params Optional search query and ownership filter for server-side filtering
 */
export const getVaults = async (params?: GetVaultsParams): Promise<VaultsListResponse> => {
  const queryParams: Record<string, string> = {};
  if (params?.search) {
    queryParams.search = params.search;
  }
  if (params?.ownership) {
    queryParams.ownership = params.ownership;
  }
  const response = await api.get<VaultsListResponse>('/vaults/', { params: queryParams });
  return response.data;
};

/**
 * Get a single vault by ID
 */
export const getVault = async (id: string): Promise<Vault> => {
  const response = await api.get<Vault>(`/vaults/${id}/`);
  return response.data;
};

/**
 * Create a new vault
 */
export const createVault = async (data: CreateVaultRequest): Promise<Vault> => {
  const response = await api.post<Vault>('/vaults/', data);
  return response.data;
};

/**
 * Update an existing vault
 */
export const updateVault = async (id: string, data: UpdateVaultRequest): Promise<Vault> => {
  const response = await api.patch<Vault>(`/vaults/${id}/`, data);
  return response.data;
};

/**
 * Delete a vault permanently
 */
export const deleteVault = async (id: string): Promise<void> => {
  await api.delete(`/vaults/${id}/`);
};

/**
 * Archive a vault (soft delete)
 */
export const archiveVault = async (id: string): Promise<Vault> => {
  const response = await api.patch<Vault>(`/vaults/${id}/`, { is_archived: true });
  return response.data;
};

/**
 * Get all members of a vault
 */
export const getVaultMembers = async (vaultId: string): Promise<VaultMembersListResponse> => {
  const response = await api.get<VaultMembersListResponse>(`/vaults/${vaultId}/members/`);
  return response.data;
};

/**
 * Add an existing user to a vault by email/username
 */
export const addVaultMember = async (vaultId: string, data: AddMemberRequest): Promise<VaultMember> => {
  const response = await api.post<VaultMember>(`/vaults/${vaultId}/members/`, data);
  return response.data;
};

/**
 * Invite a new user to a vault by email (sends invitation)
 */
export const inviteVaultMember = async (vaultId: string, data: InviteMemberRequest): Promise<VaultMember> => {
  const response = await api.post<VaultMember>(`/vaults/${vaultId}/members/invite/`, data);
  return response.data;
};

/**
 * Update a member's role in a vault
 */
export const updateMemberRole = async (
  vaultId: string,
  memberId: string,
  data: UpdateMemberRoleRequest
): Promise<VaultMember> => {
  const response = await api.patch<VaultMember>(`/vaults/${vaultId}/members/${memberId}/`, data);
  return response.data;
};

/**
 * Remove a member from a vault
 */
export const removeMember = async (vaultId: string, memberId: string): Promise<void> => {
  await api.delete(`/vaults/${vaultId}/members/${memberId}/`);
};

/**
 * Get AI-generated insights for a vault
 */
export const getVaultInsights = async (vaultId: string): Promise<VaultInsights> => {
  const response = await api.get<VaultInsights>(`/vaults/${vaultId}/insights/`);
  return response.data;
};

/**
 * Get all conversations for a vault
 */
export const getConversations = async (vaultId: string): Promise<Conversation[]> => {
  const response = await api.get<Conversation[]>(`/vaults/${vaultId}/conversations/`);
  return response.data;
};

/**
 * Get a specific conversation with full message history
 */
export const getConversation = async (vaultId: string, conversationId: number): Promise<ConversationDetail> => {
  const response = await api.get<ConversationDetail>(`/vaults/${vaultId}/conversations/${conversationId}/`);
  return response.data;
};

/**
 * Ask a question about vault contents
 */
export const askQuestion = async (vaultId: string, data: AskQuestionRequest): Promise<AskQuestionResponse> => {
  const response = await api.post<AskQuestionResponse>(`/vaults/${vaultId}/ask/`, data);
  return response.data;
};
