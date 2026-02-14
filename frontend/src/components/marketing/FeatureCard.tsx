import { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  icon: LucideIcon
  title: string
  description: string
}

export default function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <div className="group relative bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all duration-300">
      {/* Watermark icon in background */}
      <div className="absolute inset-0 flex items-center justify-center opacity-5 group-hover:opacity-10 transition-opacity duration-300 overflow-hidden">
        <Icon className="w-32 h-32 text-white" />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Icon container with orange glow */}
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br from-[#F7931A] to-[#EA580C] mb-4 shadow-[0_0_20px_-5px_rgba(247,147,26,0.6)]">
          <Icon className="w-7 h-7 text-white" />
        </div>

        {/* Title */}
        <h3 className="text-xl font-bold text-white mb-3 font-heading">
          {title}
        </h3>

        {/* Description */}
        <p className="text-[#94A3B8] leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  )
}
