'use client';

import { motion } from 'framer-motion';
import { FileText, GitMerge, Highlighter, Shield, Users, Sparkles } from 'lucide-react';
import FeatureCard from './FeatureCard';

const features = [
  {
    icon: GitMerge,
    title: 'Real-time Collaboration',
    description: 'Work together seamlessly with live updates and instant notifications as your team builds knowledge.',
  },
  {
    icon: FileText,
    title: 'Smart Citations',
    description: 'Auto-generate citations in any format with intelligent metadata extraction from your sources.',
  },
  {
    icon: Highlighter,
    title: 'PDF Annotations',
    description: 'Highlight, comment, and annotate PDFs collaboratively with your research team in real-time.',
  },
  {
    icon: Shield,
    title: 'Knowledge Vaults',
    description: 'Organize sources into secure, shareable repositories with granular access control.',
  },
  {
    icon: Users,
    title: 'Team Permissions',
    description: 'Manage who can view, contribute, or own research vaults with role-based access control.',
  },
  {
    icon: Sparkles,
    title: 'AI Insights',
    description: 'Get intelligent summaries, key insights, and cross-reference suggestions powered by AI.',
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export function FeaturesSection() {
  return (
    <section className="py-24 bg-[#030304]" id="features">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Section Heading */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-heading font-bold mb-4">
            Everything You Need to{' '}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              Collaborate
            </span>
          </h2>
          <p className="text-lg text-[#94A3B8] max-w-2xl mx-auto">
            Powerful features designed for modern research teams working on complex projects
          </p>
        </div>

        {/* Features Grid */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-100px' }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          {features.map((feature, index) => (
            <motion.div key={index} variants={item}>
              <FeatureCard
                icon={feature.icon}
                title={feature.title}
                description={feature.description}
              />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
