import Link from 'next/link';
import { Check, X } from 'lucide-react';

interface Feature {
  name: string;
  included: boolean;
}

interface PricingCardProps {
  tier: string;
  price: number;
  features: Feature[];
  isPopular?: boolean;
  ctaLink: string;
}

export default function PricingCard({
  tier,
  price,
  features,
  isPopular = false,
  ctaLink,
}: PricingCardProps) {
  return (
    <div
      className={`relative bg-[#0F1115] border rounded-2xl p-8 transition-all duration-300 hover:-translate-y-2 ${
        isPopular
          ? 'scale-105 border-[#F7931A] shadow-[0_0_40px_-10px_rgba(247,147,26,0.5)]'
          : 'border-white/10 hover:border-white/20'
      }`}
    >
      {isPopular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm px-4 py-1 rounded-full shadow-lg">
          Popular
        </div>
      )}

      <div className="text-center mb-8">
        <h3 className="font-heading text-2xl font-bold mb-2">{tier}</h3>
        <div className="flex items-baseline justify-center gap-1">
          <span className="text-5xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            ${price}
          </span>
          {price > 0 && <span className="text-[#94A3B8]">/month</span>}
        </div>
      </div>

      <ul className="space-y-4 mb-8">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start gap-3">
            {feature.included ? (
              <Check className="w-5 h-5 text-[#F7931A] flex-shrink-0 mt-0.5" />
            ) : (
              <X className="w-5 h-5 text-white/20 flex-shrink-0 mt-0.5" />
            )}
            <span
              className={`text-sm ${
                feature.included ? 'text-white' : 'text-white/40'
              }`}
            >
              {feature.name}
            </span>
          </li>
        ))}
      </ul>

      <Link
        href={ctaLink}
        className={`block w-full text-center font-bold uppercase tracking-wider rounded-full px-6 py-3 transition-all duration-300 ${
          isPopular
            ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105'
            : 'border-2 border-white/20 text-white hover:border-[#F7931A] hover:text-[#F7931A]'
        }`}
      >
        Get Started
      </Link>
    </div>
  );
}
