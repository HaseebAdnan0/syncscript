'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import TestimonialCard from './TestimonialCard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const testimonials = [
  {
    name: 'Dr. Sarah Chen',
    title: 'Associate Professor',
    institution: 'Stanford University',
    quote:
      'SyncScript transformed our research workflow. Real-time collaboration and smart citations saved our team hundreds of hours on our meta-analysis project.',
  },
  {
    name: 'Marcus Rodriguez',
    title: 'PhD Candidate',
    institution: 'MIT',
    quote:
      'The PDF annotation features are incredible. Being able to highlight, comment, and cross-reference sources with my research team has made literature reviews so much more efficient.',
  },
  {
    name: 'Dr. Emily Watson',
    title: 'Research Director',
    institution: 'Oxford University',
    quote:
      'Knowledge Vaults are a game-changer for managing complex research projects. Our lab now has a single source of truth for all our citations and sources.',
  },
  {
    name: 'Prof. James Liu',
    title: 'Professor of Physics',
    institution: 'Caltech',
    quote:
      'The AI-powered metadata extraction is phenomenal. It automatically organized thousands of papers and generated perfect citations in seconds. This is the future of academic research.',
  },
];

export default function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextTestimonial = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  const goToTestimonial = (index: number) => {
    setCurrentIndex(index);
  };

  return (
    <section className="relative py-24 bg-[#030304]">
      <div className="container mx-auto max-w-7xl px-6">
        {/* Section Heading */}
        <div className="text-center mb-16">
          <h2 className="font-heading text-4xl md:text-5xl font-bold text-white mb-4">
            Trusted by{' '}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              Researchers
            </span>
          </h2>
          <p className="text-[#94A3B8] text-lg max-w-2xl mx-auto">
            See what researchers from top institutions say about SyncScript
          </p>
        </div>

        {/* Desktop: 3-column grid (hidden on mobile) */}
        <div className="hidden md:grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.slice(0, 3).map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-100px' }}
              transition={{ duration: 0.6, delay: index * 0.15 }}
            >
              <TestimonialCard {...testimonial} />
            </motion.div>
          ))}
        </div>

        {/* Mobile: Carousel (visible only on mobile) */}
        <div className="md:hidden">
          <div className="relative">
            {/* Carousel Container */}
            <div className="overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentIndex}
                  initial={{ opacity: 0, x: 100 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ duration: 0.3 }}
                >
                  <TestimonialCard {...testimonials[currentIndex]} />
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Navigation Arrows */}
            <div className="flex justify-between items-center mt-6">
              <button
                onClick={prevTestimonial}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
                aria-label="Previous testimonial"
              >
                <ChevronLeft className="w-5 h-5 text-white" />
              </button>

              {/* Dot Indicators */}
              <div className="flex gap-2">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => goToTestimonial(index)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      index === currentIndex
                        ? 'bg-[#F7931A] w-8'
                        : 'bg-white/20 hover:bg-white/40'
                    }`}
                    aria-label={`Go to testimonial ${index + 1}`}
                  />
                ))}
              </div>

              <button
                onClick={nextTestimonial}
                className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-[#F7931A]/50 transition-all"
                aria-label="Next testimonial"
              >
                <ChevronRight className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
