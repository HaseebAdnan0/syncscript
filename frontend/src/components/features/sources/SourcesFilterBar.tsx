'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter, usePathname } from 'next/navigation'
import { Filter, X } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { SourceType } from '@/lib/types/sources'

interface SourcesFilterBarProps {
  vaultMembers?: Array<{ id: string; username: string }>
}

export function SourcesFilterBar({ vaultMembers = [] }: SourcesFilterBarProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [selectedType, setSelectedType] = useState<SourceType | 'all'>('all')
  const [selectedDate, setSelectedDate] = useState<string>('any')
  const [selectedContributor, setSelectedContributor] = useState<string>('all')

  // Initialize from URL params on mount
  useEffect(() => {
    const typeParam = searchParams.get('type')
    const dateParam = searchParams.get('date')
    const contributorParam = searchParams.get('contributor')

    if (typeParam) setSelectedType(typeParam as SourceType | 'all')
    if (dateParam) setSelectedDate(dateParam)
    if (contributorParam) setSelectedContributor(contributorParam)
  }, [searchParams])

  const updateFilters = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())

    if (value === 'all' || value === 'any') {
      params.delete(key)
    } else {
      params.set(key, value)
    }

    router.push(`${pathname}?${params.toString()}`)
  }

  const handleTypeChange = (type: SourceType | 'all') => {
    setSelectedType(type)
    updateFilters('type', type === 'all' ? 'all' : type.toString())
  }

  const handleDateChange = (date: string) => {
    setSelectedDate(date)
    updateFilters('date', date)
  }

  const handleContributorChange = (contributor: string) => {
    setSelectedContributor(contributor)
    updateFilters('contributor', contributor)
  }

  const clearAllFilters = () => {
    setSelectedType('all')
    setSelectedDate('any')
    setSelectedContributor('all')
    router.push(pathname)
  }

  const hasActiveFilters =
    selectedType !== 'all' || selectedDate !== 'any' || selectedContributor !== 'all'

  const typeLabels: Record<string, string> = {
    all: 'All Types',
    [SourceType.URL]: 'URL',
    [SourceType.PDF]: 'PDF',
    [SourceType.CITATION]: 'Citation',
    [SourceType.ARTICLE]: 'Article',
  }

  const dateOptions = [
    { value: 'any', label: 'Any Time' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'custom', label: 'Custom Range' },
  ]

  return (
    <div className="flex items-center gap-4 mb-6">
      <div className="flex items-center gap-2 text-sm text-[#94A3B8]">
        <Filter className="w-4 h-4" />
        <span>Filter by:</span>
      </div>

      {/* Type Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="backdrop-blur-lg bg-white/5 border border-white/10 hover:border-[#F7931A]/50 transition-all rounded-full px-4 py-2 text-white"
          >
            {selectedType === 'all' ? 'All Types' : typeLabels[selectedType]}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="backdrop-blur-lg bg-[#0F1115] border border-white/10 rounded-xl">
          <DropdownMenuItem
            onClick={() => handleTypeChange('all')}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            All Types
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => handleTypeChange(SourceType.URL)}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            URL
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => handleTypeChange(SourceType.PDF)}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            PDF
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => handleTypeChange(SourceType.CITATION)}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            Citation
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => handleTypeChange(SourceType.ARTICLE)}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            Article
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Date Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="backdrop-blur-lg bg-white/5 border border-white/10 hover:border-[#F7931A]/50 transition-all rounded-full px-4 py-2 text-white"
          >
            {dateOptions.find((opt) => opt.value === selectedDate)?.label || 'Any Time'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="backdrop-blur-lg bg-[#0F1115] border border-white/10 rounded-xl">
          {dateOptions.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onClick={() => handleDateChange(option.value)}
              className="text-white hover:bg-white/10 cursor-pointer"
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Contributor Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="backdrop-blur-lg bg-white/5 border border-white/10 hover:border-[#F7931A]/50 transition-all rounded-full px-4 py-2 text-white"
          >
            {selectedContributor === 'all'
              ? 'All Contributors'
              : vaultMembers.find((m) => m.id === selectedContributor)?.username ||
                'All Contributors'}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="backdrop-blur-lg bg-[#0F1115] border border-white/10 rounded-xl">
          <DropdownMenuItem
            onClick={() => handleContributorChange('all')}
            className="text-white hover:bg-white/10 cursor-pointer"
          >
            All Contributors
          </DropdownMenuItem>
          {vaultMembers.map((member) => (
            <DropdownMenuItem
              key={member.id}
              onClick={() => handleContributorChange(member.id)}
              className="text-white hover:bg-white/10 cursor-pointer"
            >
              {member.username}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Clear Filters Button */}
      {hasActiveFilters && (
        <Button
          onClick={clearAllFilters}
          variant="ghost"
          className="text-[#F7931A] hover:text-[#FFD600] transition-colors flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          Clear Filters
        </Button>
      )}
    </div>
  )
}
