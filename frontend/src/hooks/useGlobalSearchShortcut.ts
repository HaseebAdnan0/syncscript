import { useEffect, useState } from 'react';

interface UseGlobalSearchShortcutReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

/**
 * Hook to handle global Cmd+K (Mac) / Ctrl+K (Windows) keyboard shortcut for search.
 * Prevents default browser behavior and only triggers when not in input/textarea.
 */
export function useGlobalSearchShortcut(): UseGlobalSearchShortcutReturn {
  const [isOpen, setIsOpen] = useState(false);

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);
  const toggle = () => setIsOpen((prev) => !prev);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Detect platform for correct modifier key (Meta for Mac, Ctrl for Windows/Linux)
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const isShortcut = isMac ? e.metaKey && e.key === 'k' : e.ctrlKey && e.key === 'k';

      if (!isShortcut) return;

      // Only trigger when not in input/textarea to avoid interfering with user typing
      const target = e.target as HTMLElement;
      const isInputElement =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable;

      if (isInputElement) return;

      // Prevent default browser behavior (e.g., Chrome's address bar focus)
      e.preventDefault();

      // Toggle search modal
      toggle();
    };

    window.addEventListener('keydown', handleKeyDown);

    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return { isOpen, open, close, toggle };
}
