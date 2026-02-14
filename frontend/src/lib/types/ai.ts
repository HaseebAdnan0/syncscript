/**
 * AI Usage Statistics
 */
export interface AIUsageStats {
  requests_today: number;
  requests_limit: number;
  tokens_today: number;
  resets_at: string; // ISO timestamp
}
