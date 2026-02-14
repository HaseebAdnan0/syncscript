'use client';

import { useEffect, useState } from 'react';
import { LayoutDashboard, FileText, MessageSquare } from 'lucide-react';

interface DashboardStats {
  vaults_count: number;
  sources_count: number;
  annotations_this_week: number;
}

export function WelcomeHeader() {
  const [greeting, setGreeting] = useState('');
  const [firstName, setFirstName] = useState('');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Get time-based greeting
    const hour = new Date().getHours();
    let timeGreeting = '';
    if (hour >= 5 && hour < 12) {
      timeGreeting = 'Good morning';
    } else if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else {
      timeGreeting = 'Good evening';
    }
    setGreeting(timeGreeting);

    // TODO: Get user's first name from auth context
    setFirstName('User');

    // Fetch dashboard stats
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/dashboard/stats/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mb-12">
      {/* Greeting */}
      <h1 className="text-4xl md:text-5xl font-bold mb-8">
        <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
          {greeting}, {firstName}
        </span>
      </h1>

      {/* Quick Stats */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse"
            >
              <div className="h-10 w-10 bg-white/10 rounded-full mb-4" />
              <div className="h-8 bg-white/10 rounded mb-2" />
              <div className="h-4 bg-white/10 rounded w-24" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Vaults Count */}
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 rounded-full flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 text-[#F7931A]" />
              </div>
              <div>
                <p className="text-3xl font-bold text-white">
                  {stats?.vaults_count ?? 0}
                </p>
                <p className="text-sm text-[#94A3B8]">Vaults</p>
              </div>
            </div>
          </div>

          {/* Sources Count */}
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 rounded-full flex items-center justify-center">
                <FileText className="w-6 h-6 text-[#F7931A]" />
              </div>
              <div>
                <p className="text-3xl font-bold text-white">
                  {stats?.sources_count ?? 0}
                </p>
                <p className="text-sm text-[#94A3B8]">Sources</p>
              </div>
            </div>
          </div>

          {/* Annotations This Week */}
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 rounded-full flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-[#F7931A]" />
              </div>
              <div>
                <p className="text-3xl font-bold text-white">
                  {stats?.annotations_this_week ?? 0}
                </p>
                <p className="text-sm text-[#94A3B8]">Annotations This Week</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
