export function HeroBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Base dark background */}
      <div className="absolute inset-0 bg-[#030304]" />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }}
      />

      {/* Radial gradient vignette fading to edges */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(
              ellipse 80% 50% at 50% 50%,
              transparent 0%,
              rgba(3, 3, 4, 0.8) 70%,
              #030304 100%
            )
          `,
        }}
      />
    </div>
  );
}
