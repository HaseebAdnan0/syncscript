// Vault role enum
export enum VaultRole {
  OWNER = 'OWNER',
  CONTRIBUTOR = 'CONTRIBUTOR',
  VIEWER = 'VIEWER',
}

// Vault member type
export interface VaultMember {
  id: number;
  vault_id: number;
  user_id: number;
  user_email: string;
  user_name: string;
  role: VaultRole;
  joined_at: string;
  is_pending?: boolean; // For invited users who haven't joined yet
}

// Storage usage info
export interface StorageUsage {
  used_bytes: number;
  limit_bytes: number;
  percentage: number;
  warning: boolean;
  file_count: number;
}

// Main vault type
export interface Vault {
  id: number;
  name: string;
  description: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  source_count: number;
  member_count: number;
  user_role: VaultRole; // Current user's role in this vault
  last_activity?: string;
  storage_usage?: StorageUsage; // Storage quota information
}

// Request/Response types for API
export interface CreateVaultRequest {
  name: string;
  description?: string;
}

export interface UpdateVaultRequest {
  name?: string;
  description?: string;
}

export interface AddMemberRequest {
  email: string;
  role: VaultRole;
}

export interface InviteMemberRequest {
  email: string;
  role: VaultRole;
}

export interface UpdateMemberRoleRequest {
  role: VaultRole;
}

// List response type
export interface VaultsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Vault[];
}

export interface VaultMembersListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: VaultMember[];
}

// AI Insights types
export interface Theme {
  name: string;
  weight: number;
  source_count: number;
}

export interface CrossReference {
  sources: string[];
  connection: string;
}

export interface VaultInsights {
  themes: Theme[];
  research_gaps: string[];
  cross_references: CrossReference[];
  suggested_searches: string[];
  generated_at: string;
}

// Chat/Conversation types
export interface ChatCitation {
  source_id: number;
  source_title: string;
  excerpt: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources_cited: ChatCitation[];
  created_at: string;
}

export interface Conversation {
  id: number;
  vault_id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  preview: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface AskQuestionRequest {
  question: string;
  conversation_id?: number;
}

export interface AskQuestionResponse {
  answer: string;
  citations: ChatCitation[];
  conversation_id: number;
}
