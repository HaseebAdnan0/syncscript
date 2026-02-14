'use client';

import React from 'react';
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/dialog';
import GradientButton from '@/components/ui/GradientButton';
import { Database, Users, FileText } from 'lucide-react';

interface WelcomeModalProps {
  isOpen: boolean;
  userName: string;
  onGetStarted: () => void | Promise<void>;
}

const WelcomeModal: React.FC<WelcomeModalProps> = ({ isOpen, userName, onGetStarted }) => {
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="max-w-2xl bg-[#0F1115] border border-white/10 backdrop-blur-lg sm:max-w-[90vw]">
        <DialogHeader>
          <h2 className="text-4xl font-bold text-center mb-2 bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            Welcome to SyncScript, {userName}!
          </h2>
          <p className="text-[#94A3B8] text-center text-lg mt-2">
            Your collaborative research & citation engine is ready
          </p>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-8">
          {/* Feature 1: Knowledge Vaults */}
          <div className="bg-black/50 border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center mb-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]">
              <Database className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Knowledge Vaults</h3>
            <p className="text-[#94A3B8] text-sm">
              Organize your research in secure, shareable vaults with verified sources and cross-referenced citations.
            </p>
          </div>

          {/* Feature 2: Real-time Collaboration */}
          <div className="bg-black/50 border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center mb-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]">
              <Users className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Real-time Collaboration</h3>
            <p className="text-[#94A3B8] text-sm">
              Work together with your team in real-time. Share insights, discuss findings, and build knowledge together.
            </p>
          </div>

          {/* Feature 3: Annotations & Citations */}
          <div className="bg-black/50 border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center mb-4 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Annotations & Citations</h3>
            <p className="text-[#94A3B8] text-sm">
              Annotate PDFs, manage citations, and extract metadata automatically with AI-powered tools.
            </p>
          </div>
        </div>

        <div className="flex justify-center mt-6">
          <GradientButton onClick={onGetStarted} className="px-8 py-4 text-lg">
            Let's Get Started
          </GradientButton>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WelcomeModal;
