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

export interface Source {
  id: number;
  vault: number;
  type: SourceType;
  url: string;
  title: string;
  metadata: SourceMetadata;
  contributor: {
    id: number;
    username: string;
    email: string;
  };
  createdAt: string;
  updatedAt: string;
}

// Request types
export interface CreateSourceRequest {
  vault: number;
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
