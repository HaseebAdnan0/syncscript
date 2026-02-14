import { apiClient } from './client';
import type {
  SearchResponse,
  SearchSuggestion,
  SearchHistory,
  SearchFilters,
} from '../types/search';

/**
 * Search across vaults, sources, and annotations
 */
export async function search(
  query: string,
  filters?: SearchFilters
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });

  if (filters?.type) {
    params.append('type', filters.type);
  }

  if (filters?.vault_id) {
    params.append('vault_id', filters.vault_id);
  }

  if (filters?.limit) {
    params.append('limit', filters.limit.toString());
  }

  const response = await apiClient.get<SearchResponse>(
    `/search/?${params.toString()}`
  );

  return response.data;
}

/**
 * Get search suggestions for autocomplete
 */
export async function getSuggestions(query: string): Promise<SearchSuggestion[]> {
  const params = new URLSearchParams({ q: query });

  const response = await apiClient.get<SearchSuggestion[]>(
    `/search/suggestions/?${params.toString()}`
  );

  return response.data;
}

/**
 * Get recent searches for the authenticated user
 */
export async function getRecentSearches(): Promise<SearchHistory[]> {
  const response = await apiClient.get<SearchHistory[]>('/search/recent/');
  return response.data;
}

/**
 * Clear all recent searches for the authenticated user
 */
export async function clearRecentSearches(): Promise<void> {
  await apiClient.delete('/search/recent/');
}

/**
 * Delete a single recent search entry
 */
export async function deleteRecentSearch(searchId: number): Promise<void> {
  await apiClient.delete(`/search/recent/${searchId}/`);
}
