export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section Placeholder */}
      <section className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-white mb-4">
            Collaborative Research
          </h1>
          <h2 className="text-6xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-6">
            Reimagined
          </h2>
          <p className="text-xl text-[#94A3B8] max-w-2xl mx-auto mb-8">
            Build Knowledge Vaults with your team. Share sources, annotate PDFs, and collaborate in real-time.
          </p>
          <div className="flex items-center justify-center gap-4">
            <a
              href="/register"
              className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
            >
              Start Free
            </a>
            <button className="border-2 border-white/20 text-white font-bold uppercase tracking-wider rounded-full px-8 py-4 hover:border-[#F7931A] transition-all">
              Watch Demo
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
