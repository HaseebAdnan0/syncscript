// Sources API client

import { api, handleApiError } from '@/lib/api';
import type {
  Source,
  CreateSourceRequest,
  UpdateSourceRequest,
  SourcesFilterParams,
} from '@/lib/types/sources';
import type { PaginatedResponse } from '@/lib/types/api';

/**
 * Get all sources for a vault with optional filters
 */
export const getSources = async (
  vaultId: string,
  filters?: SourcesFilterParams
): Promise<Source[]> => {
  try {
    const params = new URLSearchParams();

    // Map frontend param names to backend param names
    if (filters?.type) {
      params.append('source_type', filters.type); // Backend uses 'source_type'
    }
    if (filters?.dateFrom) {
      params.append('date_from', filters.dateFrom);
    }
    if (filters?.dateTo) {
      params.append('date_to', filters.dateTo);
    }
    if (filters?.contributor) {
      params.append('created_by', filters.contributor.toString()); // Backend uses 'created_by'
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }

    const queryString = params.toString();
    const url = `/vaults/${vaultId}/sources/${queryString ? `?${queryString}` : ''}`;

    const response = await api.get<PaginatedResponse<Source>>(url);

    // Return results array from paginated response
    return response.data.results;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get a single source by ID
 */
export const getSource = async (sourceId: number): Promise<Source> => {
  try {
    const response = await api.get<Source>(`/sources/${sourceId}/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a new source
 */
export const createSource = async (data: CreateSourceRequest): Promise<Source> => {
  try {
    const response = await api.post<Source>(`/vaults/${data.vault}/sources/`, data);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Update an existing source
 */
export const updateSource = async (
  sourceId: number,
  data: UpdateSourceRequest
): Promise<Source> => {
  try {
    const response = await api.patch<Source>(`/sources/${sourceId}/`, data);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete a source
 */
export const deleteSource = async (sourceId: number): Promise<void> => {
  try {
    await api.delete(`/sources/${sourceId}/`);
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Generate AI summary for a source
 */
export const summarizeSource = async (
  sourceId: number,
  regenerate = false
): Promise<Source> => {
  try {
    const params = new URLSearchParams();
    if (regenerate) {
      params.append('regenerate', 'true');
    }
    const queryString = params.toString();
    const url = `/sources/${sourceId}/summarize/${queryString ? `?${queryString}` : ''}`;

    const response = await api.post<Source>(url);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Preview URL metadata without creating a source
 */
export interface UrlPreviewResponse {
  url: string;
  title: string;
  authors: string[];
  abstract: string;
  publication_date: string | null;
  error: string | null;
}

export const previewUrl = async (url: string): Promise<UrlPreviewResponse> => {
  try {
    const response = await api.post<UrlPreviewResponse>('/sources/preview/', { url });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get presigned download URL for a PDF upload (forces download)
 */
export interface PDFDownloadUrlResponse {
  download_url: string;
  expires_in: number;
  filename: string;
  file_size: number;
}

export const getPdfDownloadUrl = async (pdfUploadId: string): Promise<PDFDownloadUrlResponse> => {
  try {
    const response = await api.get<PDFDownloadUrlResponse>(`/sources/pdfs/${pdfUploadId}/download-url/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get presigned view URL for a PDF upload (inline viewing in browser)
 */
export interface PDFViewUrlResponse {
  view_url: string;
  expires_in: number;
  filename: string;
  file_size: number;
}

export const getPdfViewUrl = async (pdfUploadId: string): Promise<PDFViewUrlResponse> => {
  try {
    const response = await api.get<PDFViewUrlResponse>(`/sources/pdfs/${pdfUploadId}/view-url/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};
