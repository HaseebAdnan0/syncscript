'use client';

import { useState, useEffect } from 'react';

type ViewMode = 'grid' | 'table';

const STORAGE_KEY = 'syncscript:sources-view';

export function useSourcesViewPreference(): [ViewMode, (mode: ViewMode) => void] {
  // Initialize with 'grid' default, will be replaced by localStorage value if available
  const [viewMode, setViewModeState] = useState<ViewMode>('grid');

  // Load preference from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'grid' || stored === 'table') {
      setViewModeState(stored);
    }
  }, []);

  // Setter that persists to localStorage
  const setViewMode = (mode: ViewMode) => {
    setViewModeState(mode);
    localStorage.setItem(STORAGE_KEY, mode);
  };

  return [viewMode, setViewMode];
}
