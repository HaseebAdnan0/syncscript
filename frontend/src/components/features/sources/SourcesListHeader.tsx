'use client';

import { Grid, List, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface SourcesListHeaderProps {
  sourceCount: number;
  viewMode: 'grid' | 'table';
  onViewModeChange: (mode: 'grid' | 'table') => void;
  onAddSource: () => void;
}

export function SourcesListHeader({
  sourceCount,
  viewMode,
  onViewModeChange,
  onAddSource,
}: SourcesListHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-bold font-heading text-white">Sources</h1>
        <Badge variant="default" className="bg-[#F7931A]/20 text-[#F7931A] border-[#F7931A]/30">
          {sourceCount}
        </Badge>
      </div>

      <div className="flex items-center gap-3">
        {/* View Toggle Buttons */}
        <div className="flex items-center gap-1 bg-[#0F1115] border border-white/10 rounded-lg p-1">
          <button
            onClick={() => onViewModeChange('grid')}
            className={`p-2 rounded transition-all ${
              viewMode === 'grid'
                ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_10px_-2px_rgba(234,88,12,0.5)]'
                : 'text-[#94A3B8] hover:text-white'
            }`}
            aria-label="Grid view"
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => onViewModeChange('table')}
            className={`p-2 rounded transition-all ${
              viewMode === 'table'
                ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_10px_-2px_rgba(234,88,12,0.5)]'
                : 'text-[#94A3B8] hover:text-white'
            }`}
            aria-label="Table view"
          >
            <List className="w-4 h-4" />
          </button>
        </div>

        {/* Add Source Button */}
        <Button
          onClick={onAddSource}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Source
        </Button>
      </div>
    </div>
  );
}
