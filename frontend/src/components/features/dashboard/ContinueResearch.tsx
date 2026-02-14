'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Folder, Plus, Clock } from 'lucide-react';

interface RecentVault {
  id: number;
  name: string;
  description: string;
  last_accessed_at: string | null;
  sources_count: number;
  role: string;
}

export default function ContinueResearch() {
  const [vaults, setVaults] = useState<RecentVault[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRecentVaults() {
      try {
        const response = await fetch('/api/v1/dashboard/recent-vaults/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setVaults(data);
        }
      } catch (error) {
        console.error('Failed to fetch recent vaults:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchRecentVaults();
  }, []);

  function formatRelativeTime(timestamp: string | null): string {
    if (!timestamp) return 'Never accessed';

    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return past.toLocaleDateString();
  }

  if (loading) {
    return (
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-white mb-6">Continue Research</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse"
            >
              <div className="h-6 bg-white/10 rounded w-3/4 mb-4" />
              <div className="h-4 bg-white/10 rounded w-1/2 mb-6" />
              <div className="flex gap-3">
                <div className="h-10 bg-white/10 rounded-full w-24" />
                <div className="h-10 bg-white/10 rounded-full w-32" />
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (vaults.length === 0) {
    return (
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-white mb-6">Continue Research</h2>
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-12 text-center">
          <Folder className="w-16 h-16 text-white/20 mx-auto mb-4" />
          <p className="text-white/60 text-lg mb-4">Create your first vault to get started</p>
          <Link
            href="/vaults/new"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
          >
            <Plus className="w-5 h-5" />
            New Vault
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="mb-12">
      <h2 className="text-2xl font-bold text-white mb-6">Continue Research</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {vaults.map((vault) => (
          <div
            key={vault.id}
            className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <Folder className="w-6 h-6 text-[#F7931A]" />
                <h3 className="text-lg font-bold text-white group-hover:text-[#F7931A] transition-colors">
                  {vault.name}
                </h3>
              </div>
              <span className="text-xs uppercase tracking-wider px-2 py-1 rounded-full bg-white/5 text-white/60 border border-white/10">
                {vault.role}
              </span>
            </div>

            <div className="flex items-center gap-2 text-sm text-white/60 mb-6">
              <Clock className="w-4 h-4" />
              <span>{formatRelativeTime(vault.last_accessed_at)}</span>
              <span className="text-white/40">•</span>
              <span>{vault.sources_count} sources</span>
            </div>

            <div className="flex gap-3">
              <Link
                href={`/vaults/${vault.id}`}
                className="flex-1 text-center bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm rounded-full px-4 py-2 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
              >
                Open
              </Link>
              <Link
                href={`/vaults/${vault.id}/sources/new`}
                className="flex items-center justify-center gap-2 bg-white/5 border border-white/20 text-white font-bold uppercase tracking-wider text-sm rounded-full px-4 py-2 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
              >
                <Plus className="w-4 h-4" />
                Add Source
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 text-center">
        <Link
          href="/vaults"
          className="inline-flex items-center gap-2 text-[#F7931A] hover:text-[#FFD600] font-medium transition-colors"
        >
          View all vaults
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  );
}
