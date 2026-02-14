import { useState, useEffect, useCallback } from 'react';
import type { SearchResult } from '@/lib/types/search';

interface UseSearchKeyboardNavigationProps {
  results: SearchResult[];
  isOpen: boolean;
  onSelect: (result: SearchResult) => void;
  onClose: () => void;
}

interface UseSearchKeyboardNavigationReturn {
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
  clearSelection: () => void;
}

/**
 * Hook for keyboard navigation in search results
 * - Arrow up/down moves selection through results
 * - Enter opens selected result
 * - Escape closes modal or clears selection
 * - Selection wraps at boundaries
 */
export function useSearchKeyboardNavigation({
  results,
  isOpen,
  onSelect,
  onClose,
}: UseSearchKeyboardNavigationProps): UseSearchKeyboardNavigationReturn {
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  // Reset selection when results change or modal closes
  useEffect(() => {
    if (!isOpen || results.length === 0) {
      setSelectedIndex(-1);
    }
  }, [isOpen, results.length]);

  const clearSelection = useCallback(() => {
    setSelectedIndex(-1);
  }, []);

  // Handle keyboard events
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (results.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => {
            // Wrap to first item if at end
            if (prev >= results.length - 1) {
              return 0;
            }
            return prev + 1;
          });
          break;

        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => {
            // Wrap to last item if at start or no selection
            if (prev <= 0) {
              return results.length - 1;
            }
            return prev - 1;
          });
          break;

        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < results.length) {
            const selectedResult = results[selectedIndex];
            onSelect(selectedResult);
          }
          break;

        case 'Escape':
          e.preventDefault();
          if (selectedIndex >= 0) {
            // First Escape clears selection
            clearSelection();
          } else {
            // Second Escape closes modal
            onClose();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex, onSelect, onClose, clearSelection]);

  return {
    selectedIndex,
    setSelectedIndex,
    clearSelection,
  };
}
