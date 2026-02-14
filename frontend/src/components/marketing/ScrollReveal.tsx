'use client';

import { motion, useInView, Variants } from 'framer-motion';
import { useRef, ReactNode } from 'react';

interface ScrollRevealProps {
  children: ReactNode;
  /**
   * Delay before animation starts (in seconds)
   */
  delay?: number;
  /**
   * Custom variants for animation
   */
  variants?: Variants;
  /**
   * Apply stagger animation to children
   */
  stagger?: boolean;
  /**
   * Stagger delay between children (in seconds)
   */
  staggerDelay?: number;
}

// Default fade up animation
const defaultVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 50,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: 'easeOut',
    },
  },
};

// Container variant for stagger children
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Item variant for staggered children
const itemVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 30,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: 'easeOut',
    },
  },
};

/**
 * ScrollReveal component that animates elements when they enter the viewport
 * Respects prefers-reduced-motion user preference
 */
export default function ScrollReveal({
  children,
  delay = 0,
  variants,
  stagger = false,
  staggerDelay = 0.1,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, {
    once: true, // Animation triggers only once
    margin: '-100px', // Trigger slightly before element enters viewport
  });

  // Choose appropriate variants
  const animationVariants = stagger
    ? { ...containerVariants, visible: { ...containerVariants.visible, transition: { staggerChildren: staggerDelay } } }
    : variants || defaultVariants;

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      variants={animationVariants}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  );
}

/**
 * ScrollRevealItem component for individual items in a staggered list
 * Use as direct children of ScrollReveal with stagger={true}
 */
export function ScrollRevealItem({ children }: { children: ReactNode }) {
  return <motion.div variants={itemVariants}>{children}</motion.div>;
}
