// Annotation types

export interface Author {
  id: number;
  username: string;
  email: string;
}

export interface AnnotationReply {
  id: number;
  annotation: number;
  author?: Author;
  text: string;
  createdAt: string;
  updatedAt: string;
}

export interface Annotation {
  id: number;
  source: number;
  author?: Author;
  text: string;
  pageNumber?: number;
  replies: AnnotationReply[];
  createdAt: string;
  updatedAt: string;
}

// Request types
export interface CreateAnnotationRequest {
  source: number;
  text: string;
  pageNumber?: number;
}

export interface CreateReplyRequest {
  annotation: number;
  text: string;
}

export interface UpdateAnnotationRequest {
  text?: string;
  pageNumber?: number;
}
