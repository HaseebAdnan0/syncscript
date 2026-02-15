'use client';

import Link from 'next/link';
import { Source } from '@/lib/types/sources';
import { SourceTypeBadge } from './SourceTypeBadge';
import { format } from 'date-fns';
import { MoreVertical, Eye, Edit, Trash2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

interface SourceTableRowProps {
  source: Source;
  vaultId: string;
  onEdit?: (source: Source) => void;
  onDelete?: (source: Source) => void;
}

export function SourceTableRow({ source, vaultId, onEdit, onDelete }: SourceTableRowProps) {
  return (
    <tr className="hover:bg-white/5 transition-colors border-b border-white/5">
      {/* Type Badge */}
      <td className="px-4 py-3">
        <SourceTypeBadge type={source.source_type} />
      </td>

      {/* Title (linked) */}
      <td className="px-4 py-3">
        <Link
          href={`/vaults/${vaultId}/sources/${source.id}`}
          className="text-white hover:text-[#F7931A] transition-colors font-medium"
        >
          {source.title}
        </Link>
      </td>

      {/* Contributor */}
      <td className="px-4 py-3 text-[#94A3B8] text-sm">
        {source.created_by || 'Unknown'}
      </td>

      {/* Date Added */}
      <td className="px-4 py-3 text-[#94A3B8] text-sm">
        {format(new Date(source.created_at), 'MMM d, yyyy')}
      </td>

      {/* Actions Menu */}
      <td className="px-4 py-3">
        <DropdownMenu>
          <DropdownMenuTrigger className="hover:bg-white/10 rounded p-1 transition-colors">
            <MoreVertical className="h-4 w-4 text-[#94A3B8]" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link
                href={`/vaults/${vaultId}/sources/${source.id}`}
                className="flex items-center gap-2"
              >
                <Eye className="h-4 w-4" />
                <span>View</span>
              </Link>
            </DropdownMenuItem>
            {onEdit && (
              <DropdownMenuItem onClick={() => onEdit(source)} className="flex items-center gap-2">
                <Edit className="h-4 w-4" />
                <span>Edit</span>
              </DropdownMenuItem>
            )}
            {onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => onDelete(source)}
                  className="flex items-center gap-2 text-red-400 focus:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Delete</span>
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </td>
    </tr>
  );
}
