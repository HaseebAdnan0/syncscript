'use client';

import Link from 'next/link';
import { Vault, VaultRole } from '@/lib/types/vault';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, FileText, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VaultCardProps {
  vault: Vault;
}

function getRoleBadgeStyles(role: VaultRole) {
  switch (role) {
    case VaultRole.OWNER:
      return 'bg-primary/20 text-primary border-primary/30';
    case VaultRole.CONTRIBUTOR:
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case VaultRole.VIEWER:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function VaultCard({ vault }: VaultCardProps) {
  const truncateDescription = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
  };

  return (
    <Link href={`/vaults/${vault.id}`}>
      <Card className="cursor-pointer group">
        <CardHeader>
          <div className="flex items-start justify-between gap-4 mb-2">
            <CardTitle className="group-hover:text-primary transition-colors">
              {vault.name}
            </CardTitle>
            <Badge className={cn('shrink-0', getRoleBadgeStyles(vault.user_role))}>
              {vault.user_role}
            </Badge>
          </div>
          {vault.description && (
            <CardDescription className="line-clamp-2">
              {truncateDescription(vault.description)}
            </CardDescription>
          )}
        </CardHeader>

        <CardContent>
          <div className="flex items-center gap-6 text-sm text-muted">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span>{vault.source_count} {vault.source_count === 1 ? 'source' : 'sources'}</span>
            </div>

            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <span>{vault.member_count} {vault.member_count === 1 ? 'member' : 'members'}</span>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <Clock className="w-4 h-4" />
              <span>{formatDate(vault.updated_at)}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
