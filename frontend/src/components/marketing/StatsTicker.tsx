'use client';

import { useEffect, useRef, useState } from 'react';
import { Users, FileText, TrendingUp } from 'lucide-react';
import { motion, useInView } from 'framer-motion';

interface StatItemProps {
  icon: React.ReactNode;
  value: number;
  label: string;
  suffix?: string;
}

interface PlatformStats {
  users_count: number;
  sources_count: number;
  citations_count: number;
}

function StatItem({ icon, value, label, suffix = '' }: StatItemProps) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;

    let startTime: number;
    const duration = 2000; // 2 seconds animation

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic function for smooth deceleration
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(easeOut * value));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [isInView, value]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6 }}
      className="flex flex-col items-center gap-2"
    >
      <div className="flex items-center gap-3">
        <div className="text-[#F7931A]">{icon}</div>
        <div className="text-3xl md:text-4xl font-bold font-heading text-white">
          {count.toLocaleString()}
          {suffix}
        </div>
      </div>
      <div className="text-sm md:text-base text-[#94A3B8] uppercase tracking-wider">
        {label}
      </div>
    </motion.div>
  );
}

export default function StatsTicker() {
  const [stats, setStats] = useState<PlatformStats | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${apiUrl}/dashboard/public-stats/`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch {
        // Silently fail - will use default values
      }
    }

    fetchStats();
  }, []);

  // Use real stats if available, otherwise show placeholder values
  const usersCount = stats?.users_count || 0;
  const sourcesCount = stats?.sources_count || 0;
  const citationsCount = stats?.citations_count || 0;

  return (
    <section className="border-y border-white/10 bg-[#0F1115]/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 py-12 md:py-16">
        <div className="flex flex-col md:flex-row items-center justify-between gap-12 md:gap-8">
          <StatItem
            icon={<Users className="w-8 h-8" />}
            value={usersCount}
            label="Researchers"
            suffix={usersCount > 0 ? '+' : ''}
          />
          <StatItem
            icon={<FileText className="w-8 h-8" />}
            value={sourcesCount}
            label="Sources"
            suffix={sourcesCount > 0 ? '+' : ''}
          />
          <StatItem
            icon={<TrendingUp className="w-8 h-8" />}
            value={citationsCount}
            label="Citations"
            suffix={citationsCount > 0 ? '+' : ''}
          />
        </div>
      </div>
    </section>
  );
}
