'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getVaults } from '@/lib/api/vaults';
import { ChevronDown, X } from 'lucide-react';

export interface SearchFiltersPanelFilters {
  vault_id?: string;
  date_range?: 'week' | 'month' | 'year' | 'all';
  contributor_id?: string;
}

interface SearchFiltersPanelProps {
  filters: SearchFiltersPanelFilters;
  onFiltersChange: (filters: SearchFiltersPanelFilters) => void;
}

const dateRangeOptions = [
  { value: 'all', label: 'All time' },
  { value: 'week', label: 'Past week' },
  { value: 'month', label: 'Past month' },
  { value: 'year', label: 'Past year' },
] as const;

export default function SearchFiltersPanel({ filters, onFiltersChange }: SearchFiltersPanelProps) {
  const [isVaultDropdownOpen, setIsVaultDropdownOpen] = useState(false);
  const [isDateDropdownOpen, setIsDateDropdownOpen] = useState(false);

  // Fetch user's vaults for dropdown
  const { data: vaultsData } = useQuery({
    queryKey: ['vaults'],
    queryFn: () => getVaults(),
  });

  const vaults = vaultsData?.results || [];
  const selectedVault = vaults.find((v) => v.id.toString() === filters.vault_id);
  const selectedDateRange = dateRangeOptions.find((opt) => opt.value === filters.date_range) || dateRangeOptions[0];

  const hasActiveFilters = filters.vault_id || (filters.date_range && filters.date_range !== 'all');

  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const handleVaultSelect = (vaultId: string) => {
    onFiltersChange({ ...filters, vault_id: vaultId });
    setIsVaultDropdownOpen(false);
  };

  const handleDateRangeSelect = (range: 'week' | 'month' | 'year' | 'all') => {
    const newFilters = { ...filters };
    if (range === 'all') {
      delete newFilters.date_range;
    } else {
      newFilters.date_range = range;
    }
    onFiltersChange(newFilters);
    setIsDateDropdownOpen(false);
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setIsVaultDropdownOpen(false);
      setIsDateDropdownOpen(false);
    };

    if (isVaultDropdownOpen || isDateDropdownOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }

    return undefined;
  }, [isVaultDropdownOpen, isDateDropdownOpen]);

  return (
    <div className="space-y-4 p-6 bg-[#0F1115] border border-white/10 rounded-2xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-white/80">
          Filters
        </h3>
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Clear filters
          </button>
        )}
      </div>

      {/* Filter: Vault */}
      <div className="space-y-2">
        <label className="text-xs text-white/60 uppercase tracking-wider">
          Vault
        </label>
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsVaultDropdownOpen(!isVaultDropdownOpen);
              setIsDateDropdownOpen(false);
            }}
            className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white flex items-center justify-between hover:border-[#F7931A]/50 transition-colors"
          >
            <span className={selectedVault ? 'text-white' : 'text-white/40'}>
              {selectedVault ? selectedVault.name : 'All vaults'}
            </span>
            <ChevronDown className="w-4 h-4 text-white/40" />
          </button>

          {/* Vault dropdown */}
          {isVaultDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[#0F1115] border border-white/20 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
              <button
                onClick={() => {
                  const newFilters = { ...filters };
                  delete newFilters.vault_id;
                  onFiltersChange(newFilters);
                  setIsVaultDropdownOpen(false);
                }}
                className="w-full px-4 py-2.5 text-sm text-left hover:bg-white/5 transition-colors text-white/60"
              >
                All vaults
              </button>
              {vaults.map((vault) => (
                <button
                  key={vault.id}
                  onClick={() => handleVaultSelect(vault.id.toString())}
                  className={`
                    w-full px-4 py-2.5 text-sm text-left hover:bg-white/5 transition-colors
                    ${vault.id.toString() === filters.vault_id ? 'text-[#F7931A] bg-white/5' : 'text-white'}
                  `}
                >
                  {vault.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Filter: Date range */}
      <div className="space-y-2">
        <label className="text-xs text-white/60 uppercase tracking-wider">
          Created within
        </label>
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsDateDropdownOpen(!isDateDropdownOpen);
              setIsVaultDropdownOpen(false);
            }}
            className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white flex items-center justify-between hover:border-[#F7931A]/50 transition-colors"
          >
            <span>{selectedDateRange.label}</span>
            <ChevronDown className="w-4 h-4 text-white/40" />
          </button>

          {/* Date range dropdown */}
          {isDateDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[#0F1115] border border-white/20 rounded-lg shadow-lg z-10">
              {dateRangeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleDateRangeSelect(option.value)}
                  className={`
                    w-full px-4 py-2.5 text-sm text-left hover:bg-white/5 transition-colors
                    ${option.value === selectedDateRange.value ? 'text-[#F7931A] bg-white/5' : 'text-white'}
                  `}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Note: Contributor filter removed as it would require additional backend API endpoint */}
    </div>
  );
}
