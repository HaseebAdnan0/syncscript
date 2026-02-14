import Navbar from '@/components/marketing/Navbar';
import Footer from '@/components/marketing/Footer';

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
