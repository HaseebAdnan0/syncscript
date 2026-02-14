// Search result types
export type SearchResultType = 'vault' | 'source' | 'annotation';

export interface SearchResult {
  id: string;
  type: SearchResultType;
  title: string;
  snippet: string;
  highlight: string;
  relevance: number;
  vault_id: string;
  vault_name: string;
  breadcrumb: string;
}

export interface SearchResponse {
  results: {
    vaults: SearchResult[];
    sources: SearchResult[];
    annotations: SearchResult[];
  };
  total_count: number;
  query: string;
}

// Search suggestion types
export interface SearchSuggestion {
  text: string;
  type: 'source' | 'annotation';
  count: number;
}

// Search history types
export interface SearchHistory {
  id: number;
  query: string;
  result_count: number;
  created_at: string;
}

// Search filters
export interface SearchFilters {
  type?: SearchResultType;
  vault_id?: string;
  limit?: number;
}
