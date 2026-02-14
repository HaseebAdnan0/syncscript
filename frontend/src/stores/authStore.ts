import { create } from 'zustand';
import { User } from '@/lib/types/user';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  clearUser: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user: User | null) =>
    set({
      user,
      isAuthenticated: !!user,
    }),
  clearUser: () =>
    set({
      user: null,
      isAuthenticated: false,
    }),
  setLoading: (loading: boolean) =>
    set({
      isLoading: loading,
    }),
}));
