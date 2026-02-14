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

/**
 * Get all vaults for the current user
 * @param search Optional search query for server-side filtering
 */
export const getVaults = async (search?: string): Promise<VaultsListResponse> => {
  const params = search ? { search } : {};
  const response = await api.get<VaultsListResponse>('/vaults/', { params });
  return response.data;
};

/**
 * Get a single vault by ID
 */
export const getVault = async (id: number): Promise<Vault> => {
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
export const updateVault = async (id: number, data: UpdateVaultRequest): Promise<Vault> => {
  const response = await api.patch<Vault>(`/vaults/${id}/`, data);
  return response.data;
};

/**
 * Delete a vault permanently
 */
export const deleteVault = async (id: number): Promise<void> => {
  await api.delete(`/vaults/${id}/`);
};

/**
 * Archive a vault (soft delete)
 */
export const archiveVault = async (id: number): Promise<Vault> => {
  const response = await api.patch<Vault>(`/vaults/${id}/`, { is_archived: true });
  return response.data;
};

/**
 * Get all members of a vault
 */
export const getVaultMembers = async (vaultId: number): Promise<VaultMembersListResponse> => {
  const response = await api.get<VaultMembersListResponse>(`/vaults/${vaultId}/members/`);
  return response.data;
};

/**
 * Add an existing user to a vault by email/username
 */
export const addVaultMember = async (vaultId: number, data: AddMemberRequest): Promise<VaultMember> => {
  const response = await api.post<VaultMember>(`/vaults/${vaultId}/members/`, data);
  return response.data;
};

/**
 * Invite a new user to a vault by email (sends invitation)
 */
export const inviteVaultMember = async (vaultId: number, data: InviteMemberRequest): Promise<VaultMember> => {
  const response = await api.post<VaultMember>(`/vaults/${vaultId}/members/invite/`, data);
  return response.data;
};

/**
 * Update a member's role in a vault
 */
export const updateMemberRole = async (
  vaultId: number,
  memberId: number,
  data: UpdateMemberRoleRequest
): Promise<VaultMember> => {
  const response = await api.patch<VaultMember>(`/vaults/${vaultId}/members/${memberId}/`, data);
  return response.data;
};

/**
 * Remove a member from a vault
 */
export const removeMember = async (vaultId: number, memberId: number): Promise<void> => {
  await api.delete(`/vaults/${vaultId}/members/${memberId}/`);
};

/**
 * Get AI-generated insights for a vault
 */
export const getVaultInsights = async (vaultId: number): Promise<VaultInsights> => {
  const response = await api.get<VaultInsights>(`/vaults/${vaultId}/insights/`);
  return response.data;
};

/**
 * Get all conversations for a vault
 */
export const getConversations = async (vaultId: number): Promise<Conversation[]> => {
  const response = await api.get<Conversation[]>(`/vaults/${vaultId}/conversations/`);
  return response.data;
};

/**
 * Get a specific conversation with full message history
 */
export const getConversation = async (vaultId: number, conversationId: number): Promise<ConversationDetail> => {
  const response = await api.get<ConversationDetail>(`/vaults/${vaultId}/conversations/${conversationId}/`);
  return response.data;
};

/**
 * Ask a question about vault contents
 */
export const askQuestion = async (vaultId: number, data: AskQuestionRequest): Promise<AskQuestionResponse> => {
  const response = await api.post<AskQuestionResponse>(`/vaults/${vaultId}/ask/`, data);
  return response.data;
};
