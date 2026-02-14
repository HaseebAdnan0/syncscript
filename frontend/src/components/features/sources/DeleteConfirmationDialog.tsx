import * as React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Loader2 } from 'lucide-react';

interface DeleteConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  itemType: 'source' | 'annotation' | 'reply';
  itemTitle: string;
  isLoading?: boolean;
}

export function DeleteConfirmationDialog({
  open,
  onOpenChange,
  onConfirm,
  itemType,
  itemTitle,
  isLoading = false,
}: DeleteConfirmationDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="bg-[#0F1115] border border-white/10 backdrop-blur-lg rounded-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-white font-heading text-xl">
            Delete {itemType.charAt(0).toUpperCase() + itemType.slice(1)}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-[#94A3B8]">
            Are you sure you want to delete this {itemType}?
            {itemTitle && (
              <>
                {' '}
                <span className="text-white font-medium">"{itemTitle}"</span>
              </>
            )}
            {' '}
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel
            disabled={isLoading}
            className="bg-[#0F1115] border border-white/20 text-white hover:bg-white/5 transition-all rounded-full"
          >
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
              e.preventDefault();
              onConfirm();
            }}
            disabled={isLoading}
            className="bg-red-500 hover:bg-red-600 text-white border border-red-500 transition-all rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
