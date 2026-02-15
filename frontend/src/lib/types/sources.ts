// Source types

export enum SourceType {
  URL = 'url',
  PDF = 'pdf',
  CITATION = 'citation',
  ARTICLE = 'article',
}

export interface SourceMetadata {
  title?: string;
  description?: string;
  author?: string;
  publishedDate?: string;
  favicon?: string;
  imageUrl?: string;
  contentType?: string;
  [key: string]: unknown;
}

export interface AISummary {
  abstract: string;
  key_findings: string[];
  methodology: string;
  limitations: string;
  keywords: string[];
  language?: string;
  quality_flags?: string[];
  generated_at: string;
}

export interface Source {
  id: number;
  vault: string;
  source_type: SourceType;
  url: string;
  title: string;
  description?: string;
  metadata: SourceMetadata;
  ai_summary?: AISummary | null;
  created_by: string;  // Username string from backend
  created_at: string;
  updated_at: string;
}

// Request types
export interface CreateSourceRequest {
  vault: string;
  type: SourceType;
  url: string;
  title: string;
  metadata?: SourceMetadata;
}

export interface UpdateSourceRequest {
  type?: SourceType;
  url?: string;
  title?: string;
  metadata?: SourceMetadata;
}

// Filter params for sources list
export interface SourcesFilterParams {
  type?: SourceType;
  dateFrom?: string;
  dateTo?: string;
  contributor?: number;
  search?: string;
}
