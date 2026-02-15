import { Badge } from '@/components/ui/badge';
import { Globe, FileText, Quote, Newspaper, File } from 'lucide-react';
import { SourceType } from '@/lib/types/sources';

interface SourceTypeBadgeProps {
  type: SourceType | string;
  className?: string;
}

const sourceTypeConfig: Record<
  string,
  { icon: React.ComponentType<{ className?: string }>; label: string; color: string }
> = {
  url: {
    icon: Globe,
    label: 'URL',
    color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  pdf: {
    icon: FileText,
    label: 'PDF',
    color: 'bg-red-500/20 text-red-400 border-red-500/30',
  },
  citation: {
    icon: Quote,
    label: 'Citation',
    color: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  },
  article: {
    icon: Newspaper,
    label: 'Article',
    color: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
};

// Fallback for unknown types
const defaultConfig = {
  icon: File,
  label: 'Source',
  color: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

export function SourceTypeBadge({ type, className }: SourceTypeBadgeProps) {
  const config = sourceTypeConfig[type] || defaultConfig;
  const Icon = config.icon;

  return (
    <Badge className={`inline-flex items-center gap-1.5 ${config.color} ${className}`}>
      <Icon className="h-3 w-3" />
      <span>{config.label}</span>
    </Badge>
  );
}
