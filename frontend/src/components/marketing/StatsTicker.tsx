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
  return (
    <section className="border-y border-white/10 bg-[#0F1115]/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 py-12 md:py-16">
        <div className="flex flex-col md:flex-row items-center justify-between gap-12 md:gap-8">
          <StatItem
            icon={<Users className="w-8 h-8" />}
            value={10000}
            label="Researchers"
            suffix="+"
          />
          <StatItem
            icon={<FileText className="w-8 h-8" />}
            value={50000}
            label="Sources"
            suffix="+"
          />
          <StatItem
            icon={<TrendingUp className="w-8 h-8" />}
            value={1000000}
            label="Citations"
            suffix="+"
          />
        </div>
      </div>
    </section>
  );
}
