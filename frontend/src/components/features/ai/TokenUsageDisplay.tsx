"use client";

import React from "react";

interface TokenUsageDisplayProps {
  usage: {
    requests_today: number;
    requests_limit: number;
    tokens_today: number;
    resets_at: string; // ISO timestamp
  };
}

export default function TokenUsageDisplay({ usage }: TokenUsageDisplayProps) {
  const { requests_today, requests_limit, tokens_today, resets_at } = usage;

  // Calculate usage percentage
  const usagePercentage = (requests_today / requests_limit) * 100;
  const isWarning = usagePercentage > 80;

  // Calculate time until reset
  const resetTime = new Date(resets_at);
  const now = new Date();
  const msUntilReset = resetTime.getTime() - now.getTime();
  const hoursUntilReset = Math.max(0, Math.floor(msUntilReset / (1000 * 60 * 60)));
  const minutesUntilReset = Math.max(0, Math.floor((msUntilReset % (1000 * 60 * 60)) / (1000 * 60)));

  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">AI Usage</h3>
        {isWarning && (
          <span className="px-3 py-1 bg-orange-500/20 border border-orange-500/30 rounded-full text-xs font-medium text-orange-400">
            High Usage
          </span>
        )}
      </div>

      {/* Request Usage Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-white/70">Requests Today</span>
          <span className="text-white font-medium">
            {requests_today} / {requests_limit}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isWarning
                ? "bg-gradient-to-r from-orange-600 to-red-500"
                : "bg-gradient-to-r from-[#EA580C] to-[#F7931A]"
            }`}
            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Reset Timer */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-white/70">Resets in</span>
        <span className="text-white font-medium">
          {hoursUntilReset > 0 && `${hoursUntilReset}h `}
          {minutesUntilReset}m
        </span>
      </div>

      {/* Token Count (Informational) */}
      <div className="pt-4 border-t border-white/10">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/70">Total Tokens Used</span>
          <span className="text-white/50 font-mono text-xs">
            {tokens_today.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Warning Message */}
      {isWarning && (
        <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <p className="text-xs text-orange-400">
            You've used {usagePercentage.toFixed(0)}% of your daily AI requests.
            Consider waiting until the reset for more requests.
          </p>
        </div>
      )}
    </div>
  );
}
