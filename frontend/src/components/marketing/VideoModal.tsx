"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

interface VideoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function VideoModal({ isOpen, onClose }: VideoModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-4xl z-50">
          <div className="relative bg-[#0F1115] border border-white/10 rounded-2xl overflow-hidden">
            {/* Close Button */}
            <Dialog.Close className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black/50 backdrop-blur-lg border border-white/10 hover:bg-white/10 transition-colors">
              <X className="w-5 h-5 text-white" />
            </Dialog.Close>

            {/* Video Container */}
            <div className="relative w-full aspect-video bg-black">
              {/* Placeholder for demo video - replace with actual YouTube/Vimeo embed */}
              <iframe
                className="w-full h-full"
                src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&rel=0"
                title="SyncScript Demo Video"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
