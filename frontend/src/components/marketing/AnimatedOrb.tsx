"use client";

import React from "react";

export default function AnimatedOrb() {
  return (
    <div className="relative flex items-center justify-center w-full h-full">
      {/* Animated Orb Container */}
      <div className="relative animate-float">
        {/* Main Gradient Orb */}
        <div className="w-64 h-64 md:w-80 md:h-80 lg:w-96 lg:h-96 rounded-full bg-gradient-to-br from-[#F7931A] to-[#FFD600] shadow-[0_0_80px_-10px_rgba(247,147,26,0.8)]" />

        {/* Orbital Ring 1 - Horizontal */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] border-2 border-white/20 rounded-full animate-orbit-slow" />

        {/* Orbital Ring 2 - Tilted */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] border-2 border-white/15 rounded-full animate-orbit-medium"
             style={{ transform: "translate(-50%, -50%) rotateX(60deg) rotateY(20deg)" }} />

        {/* Orbital Ring 3 - Vertical */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] border-2 border-white/10 rounded-full animate-orbit-fast"
             style={{ transform: "translate(-50%, -50%) rotateY(90deg)" }} />
      </div>
    </div>
  );
}
