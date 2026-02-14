"use client"

import { useEffect, useState } from 'react'
import { Users } from 'lucide-react'

interface Collaborator {
  user_id: number
  name: string
  avatar_url: string | null
  contributions_count: number
}

export default function TopCollaborators() {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchCollaborators() {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:8000/api/v1/dashboard/analytics/top-collaborators/', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error('Failed to fetch top collaborators')
        }

        const data = await response.json()
        setCollaborators(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchCollaborators()
  }, [])

  // Helper function to get initials from name
  function getInitials(name: string): string {
    const parts = name.trim().split(/\s+/)
    if (parts.length === 1) {
      return parts[0].substring(0, 2).toUpperCase()
    }
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }

  if (loading) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6">
        <h2 className="text-xl font-heading font-bold mb-6">Top Collaborators</h2>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 animate-pulse">
              <div className="w-12 h-12 bg-white/5 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-white/5 rounded w-32 mb-2" />
                <div className="h-3 bg-white/5 rounded w-20" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6">
        <h2 className="text-xl font-heading font-bold mb-6">Top Collaborators</h2>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    )
  }

  if (collaborators.length === 0) {
    return (
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6">
        <h2 className="text-xl font-heading font-bold mb-6">Top Collaborators</h2>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-[#F7931A] to-[#FFD600] rounded-full flex items-center justify-center mb-4">
            <Users className="w-8 h-8 text-white" />
          </div>
          <p className="text-[#94A3B8] mb-1">Invite collaborators to see who contributes most</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all">
      <h2 className="text-xl font-heading font-bold mb-6">Top Collaborators</h2>
      <div className="space-y-4">
        {collaborators.map((collaborator) => (
          <div
            key={collaborator.user_id}
            className="flex items-center gap-4 hover:bg-white/5 p-2 -m-2 rounded-lg transition-colors"
          >
            {/* Avatar */}
            <div className="relative">
              {collaborator.avatar_url ? (
                <img
                  src={collaborator.avatar_url}
                  alt={collaborator.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-r from-[#F7931A] to-[#FFD600] rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">
                    {getInitials(collaborator.name)}
                  </span>
                </div>
              )}
            </div>

            {/* Name and contributions */}
            <div className="flex-1 min-w-0">
              <h3 className="text-white font-medium truncate">
                {collaborator.name}
              </h3>
              <p className="text-[#94A3B8] text-sm">
                {collaborator.contributions_count} contribution{collaborator.contributions_count !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Contribution badge */}
            <div className="bg-gradient-to-r from-[#F7931A]/20 to-[#FFD600]/20 border border-[#F7931A]/30 rounded-full px-3 py-1">
              <span className="text-[#F7931A] font-bold text-sm">
                {collaborator.contributions_count}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
