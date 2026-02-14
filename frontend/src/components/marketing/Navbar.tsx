'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Features', href: '#features' },
    { name: 'How It Works', href: '#how-it-works' },
    { name: 'Pricing', href: '#pricing' },
  ];

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault();
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
        setIsMobileMenuOpen(false);
      }
    }
  };

  return (
    <nav
      className={`sticky top-0 z-50 border-b transition-all duration-300 ${
        isScrolled
          ? 'bg-[#0F1115]/95 backdrop-blur-lg border-white/20'
          : 'bg-transparent border-white/10'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-heading font-bold text-white hover:text-[#F7931A] transition-colors">
              SyncScript
            </Link>
          </div>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => scrollToSection(e, link.href)}
                className="text-[#94A3B8] hover:text-white transition-colors duration-200 cursor-pointer"
              >
                {link.name}
              </a>
            ))}
          </div>

          {/* Desktop CTAs */}
          <div className="hidden md:flex items-center space-x-4">
            <Link
              href="/login"
              className="text-[#94A3B8] hover:text-white transition-colors duration-200"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-2 text-sm shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all duration-300"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden text-white p-2 hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-[#0F1115] border-t border-white/10">
          <div className="px-4 py-6 space-y-4">
            {/* Mobile Nav Links */}
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => scrollToSection(e, link.href)}
                className="block text-[#94A3B8] hover:text-white transition-colors duration-200 py-2 cursor-pointer"
              >
                {link.name}
              </a>
            ))}

            {/* Mobile Divider */}
            <div className="border-t border-white/10 pt-4 space-y-3">
              <Link
                href="/login"
                className="block text-center text-[#94A3B8] hover:text-white transition-colors duration-200 py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="block text-center bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
