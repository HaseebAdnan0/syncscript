import { useCallback } from 'react';
import { api, handleApiError } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { User } from '@/lib/types/user';

interface RegisterData {
  email: string;
  password: string;
  username: string;
  first_name?: string;
  last_name?: string;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

export const useAuth = () => {
  const { setUser, clearUser, setLoading } = useAuthStore();

  /**
   * Login user with email and password
   * Updates auth store on success
   */
  const login = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      try {
        setLoading(true);
        const response = await api.post<{ user: User }>('/auth/login/', {
          email,
          password,
        });

        setUser(response.data.user);
        return { success: true };
      } catch (error) {
        const apiError = handleApiError(error);
        return { success: false, error: apiError.message };
      } finally {
        setLoading(false);
      }
    },
    [setUser, setLoading]
  );

  /**
   * Register new user and auto-login on success
   */
  const register = useCallback(
    async (data: RegisterData): Promise<AuthResult> => {
      try {
        setLoading(true);
        const response = await api.post<{ user: User }>('/auth/register/', data);

        // Auto-login: backend should set httpOnly cookie on registration
        setUser(response.data.user);
        return { success: true };
      } catch (error) {
        const apiError = handleApiError(error);
        return { success: false, error: apiError.message };
      } finally {
        setLoading(false);
      }
    },
    [setUser, setLoading]
  );

  /**
   * Logout user and clear session
   * Clears auth store and httpOnly cookies via backend
   */
  const logout = useCallback(async (): Promise<AuthResult> => {
    try {
      setLoading(true);
      await api.post('/auth/logout/');

      clearUser();
      return { success: true };
    } catch (error) {
      // Even if logout API call fails, clear local state
      clearUser();
      const apiError = handleApiError(error);
      return { success: false, error: apiError.message };
    } finally {
      setLoading(false);
    }
  }, [clearUser, setLoading]);

  /**
   * Refresh user data from backend
   * Used on app initialization to check existing session
   */
  const refreshUser = useCallback(async (): Promise<AuthResult> => {
    try {
      setLoading(true);
      const response = await api.get<User>('/auth/me/');

      setUser(response.data);
      return { success: true };
    } catch (error) {
      // If me endpoint fails, user is not authenticated
      clearUser();
      const apiError = handleApiError(error);
      return { success: false, error: apiError.message };
    } finally {
      setLoading(false);
    }
  }, [setUser, clearUser, setLoading]);

  return {
    login,
    register,
    logout,
    refreshUser,
  };
};
