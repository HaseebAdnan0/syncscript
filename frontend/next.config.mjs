/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use empty turbopack config to enable Turbopack (Next.js 16 default)
  turbopack: {},

  // Ensure proper transpilation for react-pdf
  transpilePackages: ['react-pdf'],

  // Enable standalone output for Docker deployment
  output: 'standalone',
};

export default nextConfig;
