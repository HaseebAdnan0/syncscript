export type NotificationType =
  | 'vault_invite'
  | 'member_joined'
  | 'source_added'
  | 'annotation_reply'
  | 'mention';

export type EmailDigestFrequency = 'immediate' | 'daily' | 'weekly' | 'none';

export interface Notification {
  id: string;
  user: string;
  type: NotificationType;
  title: string;
  body: string;
  data: Record<string, any>;
  read_at: string | null;
  created_at: string;
  is_read: boolean;
}

export interface NotificationPreferences {
  id: string;
  user: string;
  email_vault_activity: boolean;
  email_mentions: boolean;
  push_enabled: boolean;
  email_digest_frequency: EmailDigestFrequency;
  push_sources: boolean;
  push_annotations: boolean;
}

export interface MutedVault {
  id: string;
  user: string;
  vault: string;
  vault_id: string;
  vault_name: string;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}

export interface MarkAllReadResponse {
  count: number;
}
