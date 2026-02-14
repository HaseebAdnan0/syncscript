'use client';

import { motion } from 'framer-motion';
import { FolderPlus, Link2, Users } from 'lucide-react';

const steps = [
  {
    number: 1,
    title: 'Create Your Vault',
    description:
      'Set up a Knowledge Vault for your research project. Define your scope, invite collaborators, and establish permissions.',
    icon: FolderPlus,
    side: 'left' as const,
  },
  {
    number: 2,
    title: 'Add Sources',
    description:
      'Import URLs, PDFs, and citations. Our AI extracts metadata, generates smart citations, and organizes everything automatically.',
    icon: Link2,
    side: 'right' as const,
  },
  {
    number: 3,
    title: 'Collaborate in Real-Time',
    description:
      'Annotate documents, share insights, and build collective knowledge. See changes instantly as your team works together.',
    icon: Users,
    side: 'left' as const,
  },
];

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="relative py-24 bg-[#030304]">
      <div className="container mx-auto max-w-7xl px-6">
        {/* Section Heading */}
        <div className="text-center mb-20">
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-white mb-4">
            How It{' '}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              Works
            </span>
          </h2>
          <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
            Three simple steps to transform your research workflow
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical gradient line (desktop only) */}
          <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-[#F7931A] via-[#F7931A]/50 to-transparent" />

          {/* Steps */}
          <div className="space-y-16 lg:space-y-24">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-100px' }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                className={`relative grid lg:grid-cols-2 gap-8 lg:gap-16 items-center ${
                  step.side === 'right' ? 'lg:flex-row-reverse' : ''
                }`}
              >
                {/* Content Card (left on desktop for left steps, right for right steps) */}
                <div
                  className={`${
                    step.side === 'right'
                      ? 'lg:col-start-2 lg:text-left'
                      : 'lg:col-start-1 lg:text-right'
                  }`}
                >
                  <div className="relative bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:border-[#F7931A]/50 transition-all duration-300">
                    {/* Corner border accents */}
                    <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-[#F7931A] rounded-tl-2xl" />
                    <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-[#F7931A] rounded-br-2xl" />

                    {/* Icon (mobile/tablet only) */}
                    <div className="lg:hidden flex items-center gap-4 mb-4">
                      <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-r from-[#EA580C] to-[#F7931A] rounded-full">
                        <step.icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="font-heading text-2xl font-bold text-white">
                        {step.title}
                      </h3>
                    </div>

                    {/* Title (desktop only) */}
                    <h3 className="hidden lg:block font-heading text-2xl font-bold text-white mb-4">
                      {step.title}
                    </h3>

                    {/* Description */}
                    <p className="text-[#94A3B8] leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Numbered Node (desktop center) */}
                <div className="hidden lg:block absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="relative flex items-center justify-center">
                    {/* Outer glow ring */}
                    <div className="absolute w-20 h-20 bg-[#F7931A]/20 rounded-full blur-xl" />
                    {/* Node circle */}
                    <div className="relative flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#F7931A] to-[#FFD600] rounded-full shadow-[0_0_30px_-5px_rgba(247,147,26,0.8)] border-4 border-[#030304]">
                      <step.icon className="w-8 h-8 text-white" />
                    </div>
                  </div>
                </div>

                {/* Empty column for spacing (alternating layout) */}
                <div
                  className={`hidden lg:block ${
                    step.side === 'right' ? 'lg:col-start-1' : 'lg:col-start-2'
                  }`}
                />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
