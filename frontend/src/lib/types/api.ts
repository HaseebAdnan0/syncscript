// Common API response types

// Generic paginated response
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Generic API error response
export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

// Success response for actions
export interface SuccessResponse {
  message: string;
  data?: Record<string, unknown>;
}

// Auth-related response types
export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface LoginResponse extends TokenResponse {
  user: {
    id: number;
    email: string;
    username: string;
  };
}

// Generic list response (non-paginated)
export interface ListResponse<T> {
  results: T[];
}
