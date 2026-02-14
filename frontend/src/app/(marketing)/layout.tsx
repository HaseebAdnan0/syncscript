import Footer from '@/components/marketing/Footer';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#030304]">
      {/* Marketing Navbar */}
      <nav className="border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <a href="/" className="text-2xl font-bold text-white">
                SyncScript
              </a>
            </div>

            {/* Nav Links */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-[#94A3B8] hover:text-white transition-colors">
                Features
              </a>
              <a href="#how-it-works" className="text-[#94A3B8] hover:text-white transition-colors">
                How It Works
              </a>
              <a href="#pricing" className="text-[#94A3B8] hover:text-white transition-colors">
                Pricing
              </a>
            </div>

            {/* CTAs */}
            <div className="flex items-center space-x-4">
              <a
                href="/login"
                className="text-[#94A3B8] hover:text-white transition-colors"
              >
                Sign In
              </a>
              <a
                href="/register"
                className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-2 text-sm shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
              >
                Get Started
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>

      {/* Marketing Footer */}
      <Footer />
    </div>
  );
}
