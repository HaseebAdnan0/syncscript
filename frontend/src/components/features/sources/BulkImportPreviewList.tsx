'use client'

import React, { useState } from 'react'
import { Check, X, Trash2 } from 'lucide-react'
import { ParsedUrl } from './BulkImportModal'

interface BulkImportPreviewListProps {
  urls: ParsedUrl[]
  onImport: (selectedUrls: string[]) => void
  onCancel: () => void
  isLoading?: boolean
}

export default function BulkImportPreviewList({
  urls,
  onImport,
  onCancel,
  isLoading = false,
}: BulkImportPreviewListProps) {
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(
    new Set(urls.filter(u => u.isValid).map(u => u.url))
  )

  const validUrls = urls.filter(u => u.isValid)

  const toggleAll = () => {
    if (selectedUrls.size === validUrls.length) {
      setSelectedUrls(new Set())
    } else {
      setSelectedUrls(new Set(validUrls.map(u => u.url)))
    }
  }

  const toggleUrl = (url: string) => {
    const newSelected = new Set(selectedUrls)
    if (newSelected.has(url)) {
      newSelected.delete(url)
    } else {
      newSelected.add(url)
    }
    setSelectedUrls(newSelected)
  }

  const removeUrl = (urlToRemove: string) => {
    // Remove from selection if selected
    const newSelected = new Set(selectedUrls)
    newSelected.delete(urlToRemove)
    setSelectedUrls(newSelected)

    // Note: Parent component should handle actual removal from urls array
    // This is just optimistic UI update
  }

  const handleImport = () => {
    onImport(Array.from(selectedUrls))
  }

  return (
    <div className="space-y-4">
      {/* Header with select/deselect all */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={toggleAll}
          className="text-sm text-[#94A3B8] hover:text-white transition-colors"
        >
          {selectedUrls.size === validUrls.length ? 'Deselect All' : 'Select All'}
        </button>
        <span className="text-sm text-[#94A3B8]">
          {selectedUrls.size} of {validUrls.length} selected
        </span>
      </div>

      {/* URL List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {urls.map((parsedUrl, index) => (
          <div
            key={index}
            className="flex items-center gap-3 bg-[#0F1115] border border-white/10 rounded-lg p-3 hover:border-white/20 transition-colors"
          >
            {/* Checkbox for valid URLs */}
            {parsedUrl.isValid && (
              <input
                type="checkbox"
                checked={selectedUrls.has(parsedUrl.url)}
                onChange={() => toggleUrl(parsedUrl.url)}
                className="w-4 h-4 accent-[#F7931A] cursor-pointer"
              />
            )}

            {/* Status Icon */}
            <div className="flex-shrink-0">
              {parsedUrl.isValid ? (
                <div className="w-6 h-6 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center">
                  <Check className="w-4 h-4 text-green-500" />
                </div>
              ) : (
                <div className="w-6 h-6 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center">
                  <X className="w-4 h-4 text-red-500" />
                </div>
              )}
            </div>

            {/* URL Text */}
            <div className="flex-1 min-w-0">
              <p
                className={`font-mono text-sm truncate ${
                  parsedUrl.isValid ? 'text-white' : 'text-red-400'
                }`}
              >
                {parsedUrl.url}
              </p>
              {parsedUrl.error && (
                <p className="text-xs text-red-400 mt-1">{parsedUrl.error}</p>
              )}
            </div>

            {/* Remove Button */}
            <button
              type="button"
              onClick={() => removeUrl(parsedUrl.url)}
              className="flex-shrink-0 p-2 text-[#94A3B8] hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
              title="Remove URL"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-6 py-3 bg-[#0F1115] border border-white/20 text-white rounded-full hover:border-white/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleImport}
          disabled={selectedUrls.size === 0 || isLoading}
          className="px-6 py-3 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? 'Importing...' : `Import Selected (${selectedUrls.size})`}
        </button>
      </div>
    </div>
  )
}
