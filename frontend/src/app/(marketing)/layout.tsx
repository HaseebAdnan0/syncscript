import type { Metadata } from 'next';
import Navbar from '@/components/marketing/Navbar';
import Footer from '@/components/marketing/Footer';

export const metadata: Metadata = {
  title: 'SyncScript - Collaborative Research Reimagined',
  description: 'Build Knowledge Vaults with your team. Manage sources, annotate PDFs, and generate citations in real-time. The ultimate collaborative research platform.',
  keywords: ['research collaboration', 'knowledge management', 'citation manager', 'PDF annotations', 'academic research', 'knowledge vault'],
  authors: [{ name: 'SyncScript' }],
  creator: 'SyncScript',
  publisher: 'SyncScript',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://syncscript.com',
    siteName: 'SyncScript',
    title: 'SyncScript - Collaborative Research Reimagined',
    description: 'Build Knowledge Vaults with your team. Manage sources, annotate PDFs, and generate citations in real-time.',
    images: [
      {
        url: '/og-image.png', // Placeholder - 1200x630 image to be added
        width: 1200,
        height: 630,
        alt: 'SyncScript - Collaborative Research Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SyncScript - Collaborative Research Reimagined',
    description: 'Build Knowledge Vaults with your team. Manage sources, annotate PDFs, and generate citations in real-time.',
    images: ['/og-image.png'], // Placeholder - 1200x630 image to be added
    creator: '@syncscript',
  },
  alternates: {
    canonical: 'https://syncscript.com',
  },
  verification: {
    google: 'google-site-verification-code', // To be replaced with actual verification code
  },
};

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#030304]">
      {/* Marketing Navbar */}
      <Navbar />

      {/* Main Content */}
      <main>{children}</main>

      {/* Marketing Footer */}
      <Footer />
    </div>
  );
}
