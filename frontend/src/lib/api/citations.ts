// Citations API client

import { api, handleApiError } from '@/lib/api';

export interface CitationResponse {
  citation: string;
  citation_html: string;
  format: string;
  source: 'structured' | 'ai';
  cached: boolean;
  task_id?: string;
  status_url?: string;
}

export interface CitationTaskStatus {
  status: 'pending' | 'completed' | 'failed';
  result?: CitationResponse;
  error?: string;
}

/**
 * Generate a citation for a source
 * @param sourceId - Source ID
 * @param format - Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)
 * @returns Citation response (may be async with task_id)
 */
export const generateCitation = async (
  sourceId: number,
  format: string
): Promise<CitationResponse> => {
  try {
    const response = await api.post<CitationResponse>(
      `/citations/sources/${sourceId}/citation/`,
      { format }
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Poll citation task status for async AI citations
 * @param taskId - Celery task ID
 * @returns Task status with result if completed
 */
export const getCitationTaskStatus = async (
  taskId: string
): Promise<CitationTaskStatus> => {
  try {
    const response = await api.get<CitationTaskStatus>(
      `/citations/tasks/${taskId}/`
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Poll until citation is ready (for async AI citations)
 * @param taskId - Celery task ID
 * @param maxAttempts - Maximum polling attempts (default: 30)
 * @param intervalMs - Polling interval in ms (default: 1000)
 * @returns Completed citation response
 */
export const pollCitationTask = async (
  taskId: string,
  maxAttempts: number = 30,
  intervalMs: number = 1000
): Promise<CitationResponse> => {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const status = await getCitationTaskStatus(taskId);

    if (status.status === 'completed' && status.result) {
      return status.result;
    }

    if (status.status === 'failed') {
      throw new Error(status.error || 'Citation generation failed');
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error('Citation generation timed out');
};

/**
 * Export all citations from a vault
 * @param vaultId - Vault ID
 * @param format - Citation format (apa7, mla9, chicago17, bibtex, ieee, harvard)
 * @returns File blob for download
 */
export const exportVaultCitations = async (
  vaultId: number,
  format: string
): Promise<Blob> => {
  try {
    const response = await api.get(`/citations/vaults/${vaultId}/export/`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};
