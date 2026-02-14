import { FileText, Image, File } from 'lucide-react';

interface FileTypeIconProps {
  mimeType: string;
  size?: 'sm' | 'md' | 'lg';
  active?: boolean;
}

const sizeMap = {
  sm: 16,
  md: 24,
  lg: 32,
};

export function FileTypeIcon({ mimeType, size = 'md', active = false }: FileTypeIconProps) {
  const iconSize = sizeMap[size];
  const colorClass = active ? 'text-[#F7931A]' : 'text-[#94A3B8]';

  // Determine icon based on MIME type
  const getIcon = () => {
    if (mimeType === 'application/pdf') {
      return <FileText size={iconSize} className={colorClass} />;
    }
    if (mimeType === 'image/png' || mimeType === 'image/jpeg') {
      return <Image size={iconSize} className={colorClass} />;
    }
    return <File size={iconSize} className={colorClass} />;
  };

  return getIcon();
}
