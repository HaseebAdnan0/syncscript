import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add Authorization header
api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Flag to prevent multiple simultaneous refresh requests
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });

  failedQueue = [];
};

// Response interceptor: Handle 401 errors and token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Skip refresh for login/register endpoints
      if (originalRequest.url?.includes('/auth/login') ||
          originalRequest.url?.includes('/auth/register')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { refreshToken, setTokens } = useAuthStore.getState();

        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        // Attempt to refresh the token
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh/`,
          { refresh: refreshToken }
        );

        const { access, refresh } = response.data;
        setTokens(access, refresh || refreshToken);

        // Update the failed request's auth header
        originalRequest.headers.Authorization = `Bearer ${access}`;

        // Process queued requests
        processQueue(null);

        // Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        processQueue(refreshError);

        const { clearUser } = useAuthStore.getState();
        clearUser();

        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Custom API error type for better error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Helper function to transform axios errors into ApiError
export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string;
      message?: string;
      error?: string;
      [key: string]: unknown;
    }>;

    if (axiosError.response) {
      const { data, status } = axiosError.response;
      const message = data?.detail || data?.error || data?.message || 'An error occurred';

      // Extract field-specific errors if present
      const errors: Record<string, string[]> = {};
      Object.entries(data).forEach(([key, value]) => {
        if (Array.isArray(value) && key !== 'detail' && key !== 'message' && key !== 'error') {
          errors[key] = value as string[];
        }
      });

      return new ApiError(message, status, Object.keys(errors).length > 0 ? errors : undefined);
    }

    if (axiosError.request) {
      return new ApiError('No response from server', 0);
    }

    return new ApiError(axiosError.message);
  }

  if (error instanceof Error) {
    return new ApiError(error.message);
  }

  return new ApiError('An unknown error occurred');
};

// ============================
// Onboarding API Functions
// ============================

import { OnboardingState, OnboardingUpdateData } from '@/lib/types/onboarding';
import { Vault } from '@/lib/types/vault';

/**
 * Get current user's onboarding state
 */
export const getOnboardingState = async (): Promise<OnboardingState> => {
  const response = await api.get('/users/me/onboarding/');
  return response.data;
};

/**
 * Update current user's onboarding state
 */
export const updateOnboardingState = async (
  data: OnboardingUpdateData
): Promise<OnboardingState> => {
  const response = await api.patch('/users/me/onboarding/', data);
  return response.data;
};

/**
 * Get demo vault status (exists or not)
 */
export const getDemoVaultStatus = async (): Promise<{
  exists: boolean;
  vault_id: string | null;
}> => {
  const response = await api.get('/users/me/demo-vault/status/');
  return response.data;
};

/**
 * Create demo vault for current user
 */
export const createDemoVault = async (): Promise<Vault> => {
  const response = await api.post('/users/me/demo-vault/create/');
  return response.data;
};

/**
 * Reset demo vault to original state
 */
export const resetDemoVault = async (): Promise<Vault> => {
  const response = await api.post('/users/me/demo-vault/reset/');
  return response.data;
};

// ============================
// OAuth API Functions
// ============================

/**
 * OAuth provider types
 */
export type OAuthProvider = 'google' | 'github';

/**
 * Connected account data
 */
export interface ConnectedAccount {
  provider: OAuthProvider;
  connected_at: string;
  email: string;
  profile_picture?: string; // Google only
  username?: string;        // GitHub only
  avatar_url?: string;      // GitHub only
}

/**
 * Link OAuth account request
 */
export interface LinkOAuthAccountRequest {
  password: string;
  provider: OAuthProvider;
}

/**
 * Link OAuth account response
 */
export interface LinkOAuthAccountResponse {
  message: string;
  access: string;
  refresh: string;
}

/**
 * Complete OAuth email request
 */
export interface CompleteOAuthEmailRequest {
  email: string;
  temp_token: string;
}

/**
 * Complete OAuth email response
 */
export interface CompleteOAuthEmailResponse {
  message?: string;
  link_required?: boolean;
  access?: string;
  refresh?: string;
}

/**
 * Link OAuth account to existing user (requires password confirmation)
 */
export const linkOAuthAccount = async (
  password: string,
  provider: OAuthProvider
): Promise<LinkOAuthAccountResponse> => {
  const response = await api.post('/auth/oauth/link/', { password, provider });
  return response.data;
};

/**
 * Complete OAuth registration by providing email (for GitHub private email)
 */
export const completeOAuthEmail = async (
  email: string,
  tempToken: string
): Promise<CompleteOAuthEmailResponse> => {
  const response = await api.post('/auth/oauth/complete-email/', {
    email,
    temp_token: tempToken,
  });
  return response.data;
};

/**
 * Get list of connected OAuth accounts
 */
export const getConnectedAccounts = async (): Promise<ConnectedAccount[]> => {
  const response = await api.get('/auth/oauth/connected/');
  return response.data;
};

/**
 * Disconnect an OAuth provider from the current user's account
 */
export const disconnectOAuthProvider = async (provider: OAuthProvider): Promise<void> => {
  await api.delete(`/auth/oauth/connected/${provider}/`);
};

/**
 * Verify email response
 */
export interface VerifyEmailResponse {
  message: string;
}

/**
 * Verify email with token from email link
 */
export const verifyEmail = async (token: string): Promise<VerifyEmailResponse> => {
  const response = await api.post('/auth/verify-email/', { token });
  return response.data;
};

/**
 * Resend verification email response
 */
export interface ResendVerificationEmailResponse {
  message: string;
}

/**
 * Resend verification email to user
 * Rate limited to 3 requests per hour per IP
 */
export const resendVerificationEmail = async (
  email: string
): Promise<ResendVerificationEmailResponse> => {
  try {
    const response = await api.post('/auth/resend-verification/', { email });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 429) {
      throw new Error('Too many requests. Please wait a moment before trying again.');
    }
    throw error;
  }
};

/**
 * Request password reset email response
 */
export interface RequestPasswordResetResponse {
  message: string;
}

/**
 * Request password reset email for user
 * Rate limited to 3 requests per hour per IP
 */
export const requestPasswordReset = async (
  email: string
): Promise<RequestPasswordResetResponse> => {
  try {
    const response = await api.post('/auth/password-reset/', { email });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 429) {
      throw new Error('Too many requests. Please wait a moment before trying again.');
    }
    throw error;
  }
};

/**
 * Confirm password reset response
 */
export interface ConfirmPasswordResetResponse {
  message: string;
}

/**
 * Confirm password reset with uid, token, and new password
 */
export const confirmPasswordReset = async (
  uid: string,
  token: string,
  newPassword: string
): Promise<ConfirmPasswordResetResponse> => {
  const response = await api.post('/auth/password-reset-confirm/', {
    uid,
    token,
    new_password: newPassword,
  });
  return response.data;
};

export default api;
