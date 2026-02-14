// Annotations API client

import { api, handleApiError } from '@/lib/api';
import type {
  Annotation,
  CreateAnnotationRequest,
  CreateReplyRequest,
  UpdateAnnotationRequest,
} from '@/lib/types/annotations';

/**
 * Get all annotations for a source
 */
export const getAnnotations = async (sourceId: number): Promise<Annotation[]> => {
  try {
    const response = await api.get<Annotation[]>(`/sources/${sourceId}/annotations/`);
    return response.data;
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
