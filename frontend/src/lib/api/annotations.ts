// Annotations API client

import { api, handleApiError } from '@/lib/api';
import type {
  Annotation,
  CreateAnnotationRequest,
  CreateReplyRequest,
  UpdateAnnotationRequest,
} from '@/lib/types/annotations';

// Response type for paginated annotations
interface PaginatedResponse<T> {
  count?: number;
  next?: string | null;
  previous?: string | null;
  results?: T[];
}

/**
 * Get all annotations for a source
 */
export const getAnnotations = async (sourceId: number): Promise<Annotation[]> => {
  try {
    const response = await api.get<Annotation[] | PaginatedResponse<Annotation>>(`/sources/${sourceId}/annotations/`);
    // Handle both array and paginated response formats
    if (Array.isArray(response.data)) {
      return response.data;
    }
    // If it's a paginated response, return the results array
    if (response.data && 'results' in response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    }
    // Fallback to empty array
    return [];
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get a single annotation by ID
 */
export const getAnnotation = async (annotationId: number): Promise<Annotation> => {
  try {
    const response = await api.get<Annotation>(`/annotations/${annotationId}/`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a new annotation
 */
export const createAnnotation = async (data: CreateAnnotationRequest): Promise<Annotation> => {
  try {
    const response = await api.post<Annotation>(`/sources/${data.source}/annotations/`, data);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Update an existing annotation
 */
export const updateAnnotation = async (
  annotationId: number,
  data: UpdateAnnotationRequest
): Promise<Annotation> => {
  try {
    const response = await api.patch<Annotation>(`/annotations/${annotationId}/`, data);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete an annotation
 */
export const deleteAnnotation = async (annotationId: number): Promise<void> => {
  try {
    await api.delete(`/annotations/${annotationId}/`);
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Create a reply to an annotation
 */
export const createReply = async (data: CreateReplyRequest): Promise<Annotation> => {
  try {
    const response = await api.post<Annotation>(
      `/annotations/${data.annotation}/replies/`,
      data
    );
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete a reply
 */
export const deleteReply = async (replyId: number): Promise<void> => {
  try {
    await api.delete(`/replies/${replyId}/`);
  } catch (error) {
    throw handleApiError(error);
  }
};
