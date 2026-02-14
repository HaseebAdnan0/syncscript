import { api } from '../api';
import { AIUsageStats } from '../types/ai';

/**
 * Get current user's AI usage statistics
 */
export const getAIUsage = async (): Promise<AIUsageStats> => {
  const response = await api.get<AIUsageStats>('/ai/usage/');
  return response.data;
};
