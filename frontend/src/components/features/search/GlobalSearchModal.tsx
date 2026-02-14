'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export default function GlobalSearchModal({
  isOpen,
  onClose,
  children,
}: GlobalSearchModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        {/* Backdrop with glass morphism */}
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

        {/* Modal content */}
        <Dialog.Content
          className="fixed left-1/2 top-[40%] z-50 w-full max-w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-white/10 bg-[#0F1115]/95 backdrop-blur-lg shadow-[0_0_60px_-15px_rgba(247,147,26,0.3)] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]"
          onEscapeKeyDown={onClose}
          onPointerDownOutside={onClose}
        >
          {/* Close button */}
          <Dialog.Close
            className="absolute right-4 top-4 rounded-full p-2 text-white/60 hover:bg-white/5 hover:text-white transition-all"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </Dialog.Close>

          {/* Content */}
          <div className="p-6">
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
