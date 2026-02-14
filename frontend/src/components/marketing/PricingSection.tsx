'use client';

import { motion } from 'framer-motion';
import PricingCard from './PricingCard';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.5 },
  },
};

export default function PricingSection() {
  const pricingTiers = [
    {
      tier: 'Free',
      price: 0,
      features: [
        { name: '1 Knowledge Vault', included: true },
        { name: 'Up to 50 sources', included: true },
        { name: 'Basic annotations', included: true },
        { name: 'Community support', included: true },
        { name: 'Real-time collaboration', included: false },
        { name: 'AI-powered insights', included: false },
        { name: 'Advanced permissions', included: false },
        { name: 'Priority support', included: false },
      ],
      ctaLink: '/register?plan=free',
    },
    {
      tier: 'Pro',
      price: 12,
      features: [
        { name: '5 Knowledge Vaults', included: true },
        { name: 'Unlimited sources', included: true },
        { name: 'Advanced annotations', included: true },
        { name: 'Real-time collaboration', included: true },
        { name: 'AI-powered insights', included: true },
        { name: 'Export & integrations', included: true },
        { name: 'Advanced permissions', included: false },
        { name: 'Priority support', included: false },
      ],
      ctaLink: '/register?plan=pro',
      isPopular: true,
    },
    {
      tier: 'Team',
      price: 29,
      features: [
        { name: 'Unlimited vaults', included: true },
        { name: 'Unlimited sources', included: true },
        { name: 'Team annotations', included: true },
        { name: 'Real-time collaboration', included: true },
        { name: 'AI-powered insights', included: true },
        { name: 'Advanced permissions', included: true },
        { name: 'SSO & audit logs', included: true },
        { name: '24/7 priority support', included: true },
      ],
      ctaLink: '/register?plan=team',
    },
  ];

  return (
    <section id="pricing" className="py-24 bg-[#030304]">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="font-heading text-4xl md:text-5xl font-bold mb-4">
            Choose Your{' '}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              Research Plan
            </span>
          </h2>
          <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
            Start free and scale as your research grows. All plans include core
            collaboration features.
          </p>
        </div>

        {/* Pricing Cards Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6 lg:gap-8"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
        >
          {/* Mobile: Popular tier first, others follow */}
          {/* Desktop: Free, Pro (center/popular), Team */}
          <motion.div
            variants={itemVariants}
            className="order-2 md:order-1"
          >
            <PricingCard {...pricingTiers[0]} />
          </motion.div>
          <motion.div
            variants={itemVariants}
            className="order-1 md:order-2"
          >
            <PricingCard {...pricingTiers[1]} />
          </motion.div>
          <motion.div
            variants={itemVariants}
            className="order-3 md:order-3"
          >
            <PricingCard {...pricingTiers[2]} />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
