'use client';

interface SearchTypeFilterProps {
  activeType: 'all' | 'vaults' | 'sources' | 'annotations';
  onTypeChange: (type: 'all' | 'vaults' | 'sources' | 'annotations') => void;
  resultCounts?: {
    vaults: number;
    sources: number;
    annotations: number;
  };
}

type FilterTab = {
  id: 'all' | 'vaults' | 'sources' | 'annotations';
  label: string;
};

const filterTabs: FilterTab[] = [
  { id: 'all', label: 'All' },
  { id: 'vaults', label: 'Vaults' },
  { id: 'sources', label: 'Sources' },
  { id: 'annotations', label: 'Annotations' },
];

export default function SearchTypeFilter({
  activeType,
  onTypeChange,
  resultCounts,
}: SearchTypeFilterProps) {
  return (
    <div className="flex gap-1 border-b border-white/10">
      {filterTabs.map((tab) => {
        const isActive = activeType === tab.id;
        const count = tab.id === 'all'
          ? undefined
          : resultCounts?.[tab.id];

        return (
          <button
            key={tab.id}
            onClick={() => onTypeChange(tab.id)}
            className={`
              relative px-4 py-2.5 text-sm font-medium transition-all
              ${
                isActive
                  ? 'text-[#F7931A]'
                  : 'text-white/60 hover:text-white/80'
              }
            `}
          >
            {/* Label */}
            <span className="flex items-center gap-2">
              {tab.label}

              {/* Result count badge */}
              {count !== undefined && count > 0 && (
                <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full">
                  {count}
                </span>
              )}
            </span>

            {/* Orange underline for active tab */}
            {isActive && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#EA580C] to-[#F7931A]" />
            )}
          </button>
        );
      })}
    </div>
  );
}
