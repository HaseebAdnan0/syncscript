import { create } from 'zustand';

interface VaultsStore {
  // State
  isCreateModalOpen: boolean;
  searchQuery: string;
  activeTab: string;

  // Actions
  openCreateModal: () => void;
  closeCreateModal: () => void;
  setSearchQuery: (query: string) => void;
  setActiveTab: (tab: string) => void;
}

export const useVaultsStore = create<VaultsStore>((set) => ({
  // Initial state
  isCreateModalOpen: false,
  searchQuery: '',
  activeTab: 'sources',

  // Actions
  openCreateModal: () => set({ isCreateModalOpen: true }),
  closeCreateModal: () => set({ isCreateModalOpen: false }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
