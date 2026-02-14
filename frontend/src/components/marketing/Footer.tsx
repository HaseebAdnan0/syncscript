import Link from 'next/link';
import { Github, Twitter, Linkedin, MessageCircle } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { name: 'Features', href: '/#features' },
      { name: 'Pricing', href: '/#pricing' },
      { name: 'Demo', href: '#demo' },
      { name: 'Changelog', href: '#changelog' },
    ],
    resources: [
      { name: 'Documentation', href: '#docs' },
      { name: 'API', href: '#api' },
      { name: 'Blog', href: '#blog' },
      { name: 'Help Center', href: '#help' },
    ],
    company: [
      { name: 'About', href: '#about' },
      { name: 'Careers', href: '#careers' },
      { name: 'Contact', href: '#contact' },
      { name: 'Press', href: '#press' },
    ],
    legal: [
      { name: 'Privacy', href: '#privacy' },
      { name: 'Terms', href: '#terms' },
      { name: 'Security', href: '#security' },
      { name: 'Cookies', href: '#cookies' },
    ],
  };

  const socialLinks = [
    { name: 'Twitter', icon: Twitter, href: 'https://twitter.com/syncscript' },
    { name: 'GitHub', icon: Github, href: 'https://github.com/syncscript' },
    { name: 'LinkedIn', icon: Linkedin, href: 'https://linkedin.com/company/syncscript' },
    { name: 'Discord', icon: MessageCircle, href: 'https://discord.gg/syncscript' },
  ];

  return (
    <footer className="bg-[#0F1115] border-t border-white/10 py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Main Footer Content */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {/* Product Column */}
          <div>
            <h3 className="font-heading font-bold text-white mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-[#94A3B8] hover:text-[#F7931A] transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Column */}
          <div>
            <h3 className="font-heading font-bold text-white mb-4">Resources</h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-[#94A3B8] hover:text-[#F7931A] transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="font-heading font-bold text-white mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-[#94A3B8] hover:text-[#F7931A] transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Column */}
          <div>
            <h3 className="font-heading font-bold text-white mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-[#94A3B8] hover:text-[#F7931A] transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Social Links Row */}
        <div className="flex justify-center gap-6 mb-8 pb-8 border-b border-white/10">
          {socialLinks.map((social) => {
            const Icon = social.icon;
            return (
              <a
                key={social.name}
                href={social.href}
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[#94A3B8] hover:text-[#F7931A] hover:border-[#F7931A]/50 transition-all duration-300 hover:scale-110"
                aria-label={social.name}
              >
                <Icon className="w-5 h-5" />
              </a>
            );
          })}
        </div>

        {/* Copyright Line */}
        <div className="text-center text-[#94A3B8] text-sm">
          <p>
            © {currentYear} SyncScript. All rights reserved.{' '}
            <span className="text-white/40">Built for researchers, by researchers.</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
